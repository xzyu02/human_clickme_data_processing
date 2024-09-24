import os
import numpy as np
import pandas as pd
from PIL import Image
import json
from matplotlib import pyplot as plt
import utils


def get_medians(point_lists, mode='image', thresh=50):
    assert mode in ['image', 'category', 'all']
    medians = {}
    if mode == 'image':
        for image in point_lists:
            clickmaps = point_lists[image]
            num_clicks = []
            for clickmap in clickmaps:
                num_clicks.append(len(clickmap))
            medians[image] = np.percentile(num_clicks, thresh)
    if mode == 'category':
        for image in point_lists:
            category = image.split('/')[0]
            if category not in medians.keys():
                medians[category] = []
            clickmaps = point_lists[image]
            for clickmap in clickmaps:
                medians[category].append(len(clickmap))
        for category in medians:
            medians[category] = np.percentile(medians[category], thresh)
    if mode == 'all':
        num_clicks = []
        for image in point_lists:
            clickmaps = point_lists[image]
            for clickmap in clickmaps:
                num_clicks.append(len(clickmap))
        medians['all'] = np.percentile(num_clicks, thresh)
    return medians


if __name__ == "__main__":

    # Args
    debug = False
    config_file = os.path.join("configs", "co3d_config.yaml")
    image_dir = "CO3D_ClickMe2/"
    output_dir = "assets"
    image_output_dir = "clickme_test_images"
    percentile_thresh = 50
    center_crop = False
    display_image_keys = [
        "chair_378_44060_87918_renders_00018.png",
        "hairdryer_506_72958_141814_renders_00044.png",
        "parkingmeter_429_60366_116962_renders_00032.png",
        "cellphone_444_63640_125603_renders_00006.png",
        "backpack_374_42277_84521_renders_00046.png",
        "remote_350_36752_68568_renders_00005.png",
        "toybus_523_75464_147305_renders_00033.png",
        "bicycle_270_28792_57242_renders_00045.png",
        "laptop_606_95066_191413_renders_00006.png",
        "skateboard_579_85705_169395_renders_00039.png",
    ]

    # Load config
    config = utils.process_config(config_file)
    co3d_clickme_data = pd.read_csv(config["co3d_clickme_data"])
    blur_size = config["blur_size"]
    blur_sigma = np.sqrt(blur_size)
    min_pixels = (2 * blur_size) ** 2  # Minimum number of pixels for a map to be included following filtering
    del config["experiment_name"], config["co3d_clickme_data"]

    # Start processing
    os.makedirs(image_output_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Process files in serial
    clickmaps, _ = utils.process_clickmap_files(
        co3d_clickme_data=co3d_clickme_data,
        min_clicks=config["min_clicks"],
        max_clicks=config["max_clicks"])

    # Prepare maps
    final_clickmaps, all_clickmaps, categories, _ = utils.prepare_maps(
        final_clickmaps=clickmaps,
        blur_size=blur_size,
        blur_sigma=blur_sigma,
        image_shape=config["image_shape"],
        min_pixels=min_pixels,
        min_subjects=config["min_subjects"],
        center_crop=center_crop)
    
    # Load images
    images, image_names = [], []
    for image_file in final_clickmaps.keys():
        image_path = os.path.join(image_dir, image_file)
        image = Image.open(image_path)
        image_name = "_".join(image_path.split('/')[-2:])
        images.append(image)
        image_names.append(image_name)
    
    import pdb;pdb.set_trace()

    # Package into legacy format
    img_heatmaps = {k: {"image": image, "heatmap": heatmap} for (k, image, heatmap) in zip(final_clickmaps.keys(), images, all_clickmaps)}

    for k in display_image_keys:
        f = plt.figure()
        plt.subplot(1, 2, 1)
        plt.imshow(np.asarray(img_heatmaps[k]["image"])[:config["image_shape"][0], :config["image_shape"][1]])
        plt.axis("off")
        plt.subplot(1, 2, 2)
        plt.imshow(img_heatmaps[k]["heatmap"])
        plt.axis("off")
        plt.savefig(os.path.join(image_output_dir, k))
        if debug:
            plt.show()
        plt.close()

    np.save(os.path.join(output_dir, "co3d_clickmaps_normalized.npy"), img_heatmaps)
    medians = get_medians(all_clickmaps, 'image', thresh=percentile_thresh)
    medians.update(get_medians(all_clickmaps, 'category', thresh=percentile_thresh))
    medians.update(get_medians(all_clickmaps, 'all', thresh=percentile_thresh))
    medians_json = json.dumps(medians, indent=4)
    with open("./assets/click_medians.json", 'w') as f:
        f.write(medians_json)