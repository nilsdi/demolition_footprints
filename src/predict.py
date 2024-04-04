# %%
from torch.utils.data import DataLoader
import torch
import matplotlib
import os
import logging
import sys
from pathlib import Path
import cv2
from tqdm import tqdm
grandparent_dir = Path(__file__).parents[2]
sys.path.append(str(grandparent_dir))
sys.path.append(str(grandparent_dir / 'ISPRS_HD_NET'))
from ISPRS_HD_NET.utils.dataset import BuildingDataset  # noqa
from ISPRS_HD_NET.utils.sync_batchnorm.batchnorm import convert_model  # noqa
from ISPRS_HD_NET.model.HDNet import HighResolutionDecoupledNet  # noqa

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
matplotlib.use('tkagg')

# %%
root_dir = Path(__file__).parents[1]
data_dir = str(root_dir) + "/data/model/"
dir_checkpoint = str(grandparent_dir) + '/ISPRS_HD_NET/save_weights/pretrain/'


batchsize = 16
num_workers = 16
read_name = 'HDNet_Mass_best'
Dataset = 'NOCI'
assert Dataset in ['WHU', 'Inria', 'Mass', 'NOCI']
net = HighResolutionDecoupledNet(base_channel=48, num_classes=1)
print('Number of parameters: ', sum(p.numel() for p in net.parameters()))


def predict(net, device, batch_size, data_dir):
    dataset = BuildingDataset(
        dataset_dir=data_dir,
        training=False,
        txt_name="test.txt",
        data_name=Dataset)

    loader = DataLoader(dataset,
                        batch_size=batch_size,
                        shuffle=False,
                        num_workers=num_workers,
                        drop_last=False)

    for batch in tqdm(loader):
        imgs = batch['image']
        imgs = imgs.to(device=device, dtype=torch.float32)

        with torch.no_grad():
            pred = net(imgs)
        pred1 = (pred[0] > 0).float()
        label_pred = pred1.squeeze().cpu().int().numpy().astype('uint8') * 255
        for i in range(len(pred1)):
            img_name = batch['name'][i].split('/')[-1]
            save_path = os.path.join(data_dir, 'predictions')
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            # print('Saving to', os.path.join(save_path, img_name))
            wr = cv2.imwrite(os.path.join(save_path, img_name), label_pred[i])
            if not wr:
                print('Save failed!')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)s: %(message)s')
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logging.info(f'Using device {device}')
    if read_name != '':
        net_state_dict = net.state_dict()
        state_dict = torch.load(
            dir_checkpoint + read_name + '.pth', map_location=device)
        net_state_dict.update(state_dict)
        net.load_state_dict(net_state_dict, strict=False)
        logging.info('Model loaded from ' + read_name + '.pth')

    net = convert_model(net)
    net = torch.nn.parallel.DataParallel(net.to(device))
    torch.backends.cudnn.benchmark = True
    predict(net=net,
            batch_size=batchsize,
            device=device,
            data_dir=data_dir)