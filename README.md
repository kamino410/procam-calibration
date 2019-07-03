# procam-calibration

This repository provides the sourcecode to calibrate projector-camera system using chessboard and structured light (graycode pattern).

## Requirement

* Python
    * Python 3 is recommended
* OpenCV
    * `python -m pip install opencv-python opencv-contrib-python`
* Printed chessboard
    * You can find PDF [here](http://opencv.jp/sample/pics/chesspattern_7x10.pdf)

## How to use
### Step 1 : Generate graycode pattern

Open terminal and type the following command.

```sh
python gen_graycode_imgs.py <projector_pixel_height> <projector_pixel_width> [-graycode_step <graycode_step(default=1)>]

# example
python gen_graycode_imgs.py 1080 1920 -graycode_step 2
```

Generated pattern images will be saved in `./graycode_pattern/`.

`graycode_step` is an option to specify pixel size of a bit in the graycode.
If you get moire pattern in captured images, increase this number.

### Step 2 : Project and capture graycode pattern

Setup your system and place the chessboard in front of the projector and the camera.
Then, project the graycode pattern images from projector on it and capture it from the camera.

Although minimum required shot is one, it is recommended to capture more than 5 times with different attitude of the chessboard to improve calibration accuracy.

Captured images must be saved as `./capture_*/graycode_*.(png/jpg)`.

<table>
   <tr>
      <td><img src="./sample_data/capture_0/graycode_40.png"></td>
      <td><img src="./sample_data/capture_0/graycode_15.png"></td>
   </tr>
</table>

### Step 3 : Calibrate projector / camera parameters

After saving captured images, run the following command.

```sh
python calibrate.py <projector_pixel_height> <projector_pixel_width> <num_chess_corners_vert> <num_chess_corners_hori> <chess_block_size> <graycode_step> [-black_thr <black_thr(default=5)>] [-white_thr <white_thr(default=40)>]

# example
python calibrate.py 1080 1920 10 7 75 2 -black_thr 4 -white_thr 30
```

`chess_block_size` means length (mm/cm/m) of a block on the chessboard.
Result of the translation vector will be calculated with the unit specified here.

`black_threashold` is a threashold to determine whether a camera pixel captures projected area or not.
`white_threashold` is a threashold to specify robustness of graycode decoding.
To avoid decoding error, increase these numbers.

Calibration result will be saved as `./calibration_result.xml` (cv::FileStorage format).

## Additional Resource

This software calculates local homographies at around chessboard corners to estimate corresponding projector pixels with subpixel accuracy.
This algorithm is based on the following paper.

```
MORENO, Daniel; TAUBIN, Gabriel. Simple, accurate, and robust projector-camera calibration. In: 3D Imaging, Modeling, Processing, Visualization and Transmission (3DIMPVT), 2012 Second International Conference on. IEEE, 2012. p. 464-471.
```
