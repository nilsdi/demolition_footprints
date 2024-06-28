# %%
import torch
import logging
import matplotlib
import os
import sys
from pathlib import Path
from torch.utils.data import DataLoader
import argparse

grandparent_dir = Path(__file__).parents[4]
sys.path.append(str(grandparent_dir))
from ISPRS_HD_NET.model.HDNet import HighResolutionDecoupledNet  # type: ignore # noqa
from ISPRS_HD_NET.utils.sync_batchnorm.batchnorm import convert_model  # type: ignore # noqa
from ISPRS_HD_NET.utils.dataset import BuildingDataset  # type: ignore # noqa
from ISPRS_HD_NET.eval.eval_HDNet import eval_net  # type: ignore # noqa

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
matplotlib.use("tkagg")

root_dir = Path(__file__).parents[3]
data_dir = str(root_dir) + "/data/ML_training/"

batchsize = 16
num_workers = 8
Dataset = "NOCI"
# assert Dataset in ['WHU', 'Inria', 'Mass', 'NOCI']
net = HighResolutionDecoupledNet(base_channel=48, num_classes=1)
print("Number of parameters: ", sum(p.numel() for p in net.parameters()))


def eval_HRBR(net, device, batch_size, image_folder="train/image"):
    testdataset = BuildingDataset(
        dataset_dir=data_dir,
        training=False,
        txt_name="test.txt",
        data_name=Dataset,
        image_folder=image_folder,
    )
    test_loader = DataLoader(
        testdataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        drop_last=False,
    )
    best_score = eval_net(
        net, test_loader, device, savename=Dataset + "_" + read_name
    )  #
    print("Best iou:", best_score)
    return best_score


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="pytorch HDNet training")
    parser.add_argument("-n", "--numrun", required=True, type=int)
    parser.add_argument("-r", "--res", required=False, type=float, default=0.2)
    parser.add_argument("-bw", "--BW", required=False, type=bool, default=False)
    parser.add_argument(
        "-rn", "--read_name", required=False, type=str, default="HDNet_NOCI_0.2_C_best"
    )
    args = parser.parse_args()

    dir_checkpoint = str(root_dir) + f"/data/ML_model/save_weights/run_{args.numrun}/"
    bw_str_ = "_BW" if args.BW else ""
    image_folder = f"train{bw_str_}/image"
    read_name = args.read_name

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logging.info(f"Using device {device}")
    if read_name != "":
        net_state_dict = net.state_dict()
        state_dict = torch.load(
            dir_checkpoint + read_name + ".pth", map_location=device
        )
        net_state_dict.update(state_dict)
        net.load_state_dict(net_state_dict, strict=False)  # 删除了down1-3
        logging.info("Model loaded from " + read_name + ".pth")

    net = convert_model(net)
    net = torch.nn.parallel.DataParallel(net.to(device))
    torch.backends.cudnn.benchmark = True
    eval_HRBR(net=net, batch_size=batchsize, device=device, image_folder=image_folder)
