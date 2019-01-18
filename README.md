# procam-calibration

This repository provides the sourcecode to calibrate projector-camera system using chessboard and structured light (graycode pattern).

## How to use

### Requirement

* Python
    * Python 3 is recommended
* OpenCV
    * `python -m pip install opencv-python opencv-contrib-python`
* Printed chessboard
    * You can find PDF [here](http://oencv.jp/sample/pics/chesspattern_7x10.pdf)

### Step 1 : Generate graycode pattern

Open terminal and type the command `python gen_graycode_imgs.py <projector_pixel_height> <projector_pixel_width> [-graycode_step <graycode_step(default=1)>]`.
Generated pattern images will be saved into `./graycode_pattern/`.

`graycode_step` is a option to specify pixel size of a bit of the graycode.
If you get moire pattern in captured images, increase this number.

### Step 2 : Project pattern and capture

Setup your system and put the chessboard in front of the projector and the camera.
Then, project the graycode pattern images from projector on it and capture it from the camera.

Minimal required shot is one, however it is recommended to capture more than 5 times to improve calibration accuracy.

Captured images must be saved as './capture_*/graycode_*.(png/jpg)'.

### Step 3 : Calibrate projector / camera parameters

After saving captured images, run the command `python calibrate.py <projector_pixel_height> <projector_pixel_width> <num_chess_corners_vert> <num_chess_corners_hori> <chess_block_size> <graycode_step> [-black_thr <black_thr(default=5)>] [-white_thr <white_thr(default=40)>]`.

`chess_block_size` means size (mm/cm/m) of a block on the chessboard.
Result translation vector will be calculated with the unit specified here.

`black_threashould` is a threashold to determine whether a camera pixel captures projected area or not.
`white_threashould` is a threashold to specify robustness of graycode decoding.
To avoid decoding error, increase these numbers.

Calibration result will be saved as `./calibration_result.xml` (cv::Filestorage format).

## Additional Resource

This software calculates local homographies at around chessboard corners to estimate corresponding projector pixels with subpixel accuracy.
This algorithm is based on the following paper.

```
MORENO, Daniel; TAUBIN, Gabriel. Simple, accurate, and robust projector-camera calibration. In: 3D Imaging, Modeling, Processing, Visualization and Transmission (3DIMPVT), 2012 Second International Conference on. IEEE, 2012. p. 464-471.
```
