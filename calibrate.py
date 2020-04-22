# coding: UTF-8

import os
import os.path
import glob
import argparse
import cv2
import numpy as np
import json


def main():
    parser = argparse.ArgumentParser(
        description='Calibrate pro-cam system using chessboard and structured light projection\n'
        '  Place captured images as \n'
        '    ./ --- capture_1/ --- graycode_00.png\n'
        '        |              |- graycode_01.png\n'
        '        |              |        .\n'
        '        |              |        .\n'
        '        |              |- graycode_??.png\n'
        '        |- capture_2/ --- graycode_00.png\n'
        '        |              |- graycode_01.png\n'
        '        |      .       |        .\n'
        '        |      .       |        .\n',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument('proj_height', type=int, help='projector pixel height')
    parser.add_argument('proj_width', type=int, help='projector pixel width')
    parser.add_argument('chess_vert', type=int,
                        help='number of cross points of chessboard in vertical direction')
    parser.add_argument('chess_hori', type=int,
                        help='number of cross points of chessboard in horizontal direction')
    parser.add_argument('chess_block_size', type=float,
                        help='size of blocks of chessboard (mm or cm or m)')
    parser.add_argument('graycode_step', type=int,
                        default=1, help='step size of graycode')
    parser.add_argument('-black_thr', type=int, default=40,
                        help='threashold to determine whether a camera pixel captures projected area or not (default : 40)')
    parser.add_argument('-white_thr', type=int, default=5,
                        help='threashold to specify robustness of graycode decoding (default : 5)')
    parser.add_argument('-camera', type=str, default=str(),help='camera internal parameter json file')

    args = parser.parse_args()

    proj_shape = (args.proj_height, args.proj_width)
    chess_shape = (args.chess_vert, args.chess_hori)
    chess_block_size = args.chess_block_size
    gc_step = args.graycode_step
    black_thr = args.black_thr
    white_thr = args.white_thr

    camera_param_file = args.camera

    dirnames = sorted(glob.glob('./capture_*'))
    if len(dirnames) == 0:
        print('Directories \'./capture_*\' were not found')
        return

    print('Searching input files ...')
    used_dirnames = []
    gc_fname_lists = []
    for dname in dirnames:
        gc_fnames = sorted(glob.glob(dname + '/graycode_*'))
        if len(gc_fnames) == 0:
            continue
        used_dirnames.append(dname)
        gc_fname_lists.append(gc_fnames)
        print(' \'' + dname + '\' was found')

    camP = None
    cam_dist = None
    path, ext = os.path.splitext(camera_param_file)
    if(ext == ".json"):
        camP,cam_dist = loadCameraParam(camera_param_file)
        print('load camera parameters')
        print(camP)
        print(cam_dist)

    calibrate(used_dirnames, gc_fname_lists,
              proj_shape, chess_shape, chess_block_size, gc_step, black_thr, white_thr,
               camP, cam_dist)


def printNumpyWithIndent(tar, indentchar):
    print(indentchar + str(tar).replace('\n', '\n' + indentchar))

def loadCameraParam(json_file):
    with open(json_file, 'r') as f:
        param_data = json.load(f)
        P = param_data['camera']['P']
        d = param_data['camera']['distortion']
        return np.array(P).reshape([3,3]), np.array(d)

def calibrate(dirnames, gc_fname_lists, proj_shape, chess_shape, chess_block_size, gc_step, black_thr, white_thr, camP, camD):
    objps = np.zeros((chess_shape[0]*chess_shape[1], 3), np.float32)
    objps[:, :2] = chess_block_size * \
        np.mgrid[0:chess_shape[0], 0:chess_shape[1]].T.reshape(-1, 2)

    print('Calibrating ...')
    gc_height = int((proj_shape[0]-1)/gc_step)+1
    gc_width = int((proj_shape[1]-1)/gc_step)+1
    graycode = cv2.structured_light_GrayCodePattern.create(
        gc_width, gc_height)
    graycode.setBlackThreshold(black_thr)
    graycode.setWhiteThreshold(white_thr)

    cam_shape = cv2.imread(gc_fname_lists[0][0], cv2.IMREAD_GRAYSCALE).shape
    patch_size_half = int(np.ceil(cam_shape[1] / 180))
    print('  patch size :', patch_size_half * 2 + 1)

    cam_corners_list = []
    cam_objps_list = []
    cam_corners_list2 = []
    proj_objps_list = []
    proj_corners_list = []
    for dname, gc_filenames in zip(dirnames, gc_fname_lists):
        print('  checking \'' + dname + '\'')
        if len(gc_filenames) != graycode.getNumberOfPatternImages() + 2:
            print('Error : invalid number of images in \'' + dname + '\'')
            return None

        imgs = []
        for fname in gc_filenames:
            img = cv2.imread(fname, cv2.IMREAD_GRAYSCALE)
            if cam_shape != img.shape:
                print('Error : image size of \'' + fname + '\' is mismatch')
                return None
            imgs.append(img)
        black_img = imgs.pop()
        white_img = imgs.pop()

        res, cam_corners = cv2.findChessboardCorners(white_img, chess_shape)
        if not res:
            print('Error : chessboard was not found in \'' +
                  gc_filenames[-2] + '\'')
            return None
        cam_objps_list.append(objps)
        cam_corners_list.append(cam_corners)

        proj_objps = []
        proj_corners = []
        cam_corners2 = []
        # viz_proj_points = np.zeros(proj_shape, np.uint8)
        for corner, objp in zip(cam_corners, objps):
            c_x = int(round(corner[0][0]))
            c_y = int(round(corner[0][1]))
            src_points = []
            dst_points = []
            for dx in range(-patch_size_half, patch_size_half + 1):
                for dy in range(-patch_size_half, patch_size_half + 1):
                    x = c_x + dx
                    y = c_y + dy
                    if int(white_img[y, x]) - int(black_img[y, x]) <= black_thr:
                        continue
                    err, proj_pix = graycode.getProjPixel(imgs, x, y)
                    if not err:
                        src_points.append((x, y))
                        dst_points.append(gc_step*np.array(proj_pix))
            if len(src_points) < patch_size_half**2:
                print(
                    '    Warning : corner', c_x, c_y,
                    'was skiped because decoded pixels were too few (check your images and threasholds)')
                continue
            h_mat, inliers = cv2.findHomography(
                np.array(src_points), np.array(dst_points))
            point = h_mat@np.array([corner[0][0], corner[0][1], 1]).transpose()
            point_pix = point[0:2]/point[2]
            proj_objps.append(objp)
            proj_corners.append([point_pix])
            cam_corners2.append(corner)
            # viz_proj_points[int(round(point_pix[1])),
            #                 int(round(point_pix[0]))] = 255
        if len(proj_corners) < 3:
            print('Error : too few corners were found in \'' +
                  dname + '\' (less than 3)')
            return None
        proj_objps_list.append(np.float32(proj_objps))
        proj_corners_list.append(np.float32(proj_corners))
        cam_corners_list2.append(np.float32(cam_corners2))
        # cv2.imwrite('visualize_corners_projector_' +
        #             str(cnt) + '.png', viz_proj_points)
        # cnt += 1

    print('Initial solution of camera\'s intrinsic parameters')
    cam_rvecs = []
    cam_tvecs = []
    if(camP is None):
        ret, cam_int, cam_dist, cam_rvecs, cam_tvecs = cv2.calibrateCamera(
            cam_objps_list, cam_corners_list, cam_shape, None, None, None, None)
        print('  RMS :', ret)
    else:
        for objp, corners in zip(cam_objps_list, cam_corners_list):
            ret, cam_rvec, cam_tvec = cv2.solvePnP(objp, corners, camP, camD) 
            cam_rvecs.append(cam_rvec)
            cam_tvecs.append(cam_tvec)
            print('  RMS :', ret)
        cam_int = camP
        cam_dist = camD
    print('  Intrinsic parameters :')
    printNumpyWithIndent(cam_int, '    ')
    print('  Distortion parameters :')
    printNumpyWithIndent(cam_dist, '    ')
    print()

    print('Initial solution of projector\'s parameters')
    ret, proj_int, proj_dist, proj_rvecs, proj_tvecs = cv2.calibrateCamera(
        proj_objps_list, proj_corners_list, proj_shape, None, None, None, None)
    print('  RMS :', ret)
    print('  Intrinsic parameters :')
    printNumpyWithIndent(proj_int, '    ')
    print('  Distortion parameters :')
    printNumpyWithIndent(proj_dist, '    ')
    print()

    print('=== Result ===')
    ret, cam_int, cam_dist, proj_int, proj_dist, cam_proj_rmat, cam_proj_tvec, E, F = cv2.stereoCalibrate(
        proj_objps_list, cam_corners_list2, proj_corners_list, cam_int, cam_dist, proj_int, proj_dist, None)
    print('  RMS :', ret)
    print('  Camera intrinsic parameters :')
    printNumpyWithIndent(cam_int, '    ')
    print('  Camera distortion parameters :')
    printNumpyWithIndent(cam_dist, '    ')
    print('  Projector intrinsic parameters :')
    printNumpyWithIndent(proj_int, '    ')
    print('  Projector distortion parameters :')
    printNumpyWithIndent(proj_dist, '    ')
    print('  Rotation matrix / translation vector from camera to projector')
    print('  (they translate points from camera coord to projector coord) :')
    printNumpyWithIndent(cam_proj_rmat, '    ')
    printNumpyWithIndent(cam_proj_tvec, '    ')
    print()

    fs = cv2.FileStorage('calibration_result.xml', cv2.FILE_STORAGE_WRITE)
    fs.write('img_shape', cam_shape)
    fs.write('rms', ret)
    fs.write('cam_int', cam_int)
    fs.write('cam_dist', cam_dist)
    fs.write('proj_int', proj_int)
    fs.write('proj_dist', proj_dist)
    fs.write('rotation', cam_proj_rmat)
    fs.write('translation', cam_proj_tvec)
    fs.release()


if __name__ == '__main__':
    main()
