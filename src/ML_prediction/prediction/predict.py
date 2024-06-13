# %%
import torch
import matplotlib
import os
import logging
import sys
from pathlib import Path
from torch.utils.data import DataLoader
import cv2
from tqdm import tqdm
import argparse

grandparent_dir = Path(__file__).parents[4]
sys.path.append(str(grandparent_dir))
sys.path.append(str(grandparent_dir / "ISPRS_HD_NET"))
from ISPRS_HD_NET.utils.sync_batchnorm.batchnorm import convert_model  # type: ignore # noqa
from ISPRS_HD_NET.model.HDNet import HighResolutionDecoupledNet  # type: ignore # noqa
from ISPRS_HD_NET.utils.dataset import BuildingDataset  # type: ignore # noqa
from ISPRS_HD_NET.eval.eval_HDNet import eval_net  # type: ignore # noqa

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
matplotlib.use("tkagg")

# %%
root_dir = Path(__file__).parents[3]
data_dir = str(root_dir) + "/data/ML_prediction/"
predict = True


# %%
def predict_and_eval(
    net,
    device,
    data_dir,
    txt_name="test.txt",
    predict=True,
    prediction_folder=root_dir / "data/ML_prediction/predictions",
    image_folder="topredict/image/",
    Dataset="NOCI",
    num_workers=8,
    batchsize=16,
    read_name="",
):
    dataset = BuildingDataset(
        dataset_dir=data_dir,
        training=False,
        txt_name=txt_name,
        data_name=Dataset,
        image_folder=image_folder,
        predict=predict,
    )

    loader = DataLoader(
        dataset,
        batch_size=batchsize,
        shuffle=False,
        num_workers=num_workers,
        drop_last=False,
    )

    if predict:
        save_path = os.path.join(data_dir, prediction_folder)
        print("Saving predictions in ", save_path)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        for batch in tqdm(loader):
            imgs = batch["image"]
            imgs = imgs.to(device=device, dtype=torch.float32)

            with torch.no_grad():
                pred = net(imgs)
                pred1 = (pred[0] > 0).float()
                label_pred = pred1.squeeze().cpu().int().numpy().astype("uint8") * 255

                for i in range(len(pred1)):
                    img_name = "/".join(batch["name"][i].split("/")[-4:])
                    img_path = os.path.join(save_path, img_name)
                    os.makedirs(os.path.dirname(img_path), exist_ok=True)
                    wr = cv2.imwrite(img_path, label_pred[i])
                    if not wr:
                        print("Save failed!")
    else:
        best_score = eval_net(
            net, loader, device, savename=Dataset + "_" + read_name
        )  #
        print("Best iou:", best_score)


def predict(project_name, res=0.3, compression="i_lzw_25", BW=False):

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logging.info(f"Using device {device}")

    if BW:
        dir_checkpoint = str(root_dir) + "/data/ML_model/save_weights/run_2/"
        Dataset = "NOCI_BW"
        read_name = "HDNet_NOCI_BW_best"
    else:
        dir_checkpoint = str(root_dir) + "/data/ML_model/save_weights/run_3/"
        Dataset = "NOCI"
        read_name = "HDNet_NOCI_best"

    pred_name = f"pred_{project_name}_{res}_{compression}.txt"
    prediction_folder = "predictions/test/"

    prediction_folder = root_dir / "data/ML_prediction/predictions"
    batchsize = 16
    num_workers = 8

    image_folder = "topredict/image/"

    net = HighResolutionDecoupledNet(base_channel=48, num_classes=1)

    if read_name != "":
        net_state_dict = net.state_dict()
        state_dict = torch.load(
            dir_checkpoint + read_name + ".pth", map_location=device
        )
        net_state_dict.update(state_dict)
        net.load_state_dict(net_state_dict, strict=False)
        logging.info("Model loaded from " + read_name + ".pth")

    net = convert_model(net)
    net = torch.nn.parallel.DataParallel(net.to(device))
    torch.backends.cudnn.benchmark = True

    print("Number of parameters: ", sum(p.numel() for p in net.parameters()))

    predict_and_eval(
        net=net,
        device=device,
        data_dir=data_dir,
        predict=True,
        prediction_folder=prediction_folder,
        image_folder=image_folder,
        txt_name=pred_name,
        num_workers=num_workers,
        Dataset=Dataset,
        batchsize=batchsize,
        read_name=read_name,
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Tile raw orthophotos for prediction with ML model"
    )
    parser.add_argument("--project_name", required=True, type=str)
    parser.add_argument("--res", required=False, type=float, default=0.3)
    parser.add_argument("--compression", required=False, type=str, default="i_lzw_25")
    parser.add_argument("--BW", required=False, type=bool, default=False)
    args = parser.parse_args()
    predict(
        project_name=args.project_name,
        res=args.res,
        compression=args.compression,
        BW=args.BW,
    )
