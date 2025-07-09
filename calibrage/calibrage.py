import cv2
import numpy as np
import glob

CHECKERBOARD = (8, 4)

objp = np.zeros((CHECKERBOARD[0]*CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)

objpoints = []
imgpoints = []

images = glob.glob('/home/luca/Documents/GitHub/adaptive_robot_planning/calibrage/calibrage_image/*.jpg')
print(f"Nombre d'images trouvées : {len(images)}")

for fname in images:
    img = cv2.imread(fname)
    if img is None:
        print(f"Impossible de lire l'image {fname}")
        continue
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)
    print(f"Détection damier dans {fname} : {ret}")

    if ret:
        objpoints.append(objp)
        imgpoints.append(corners)

        cv2.drawChessboardCorners(img, CHECKERBOARD, corners, ret)
        cv2.imshow('Detection damier', img)
        cv2.waitKey(500)  # 0.5 sec par image pour voir

cv2.destroyAllWindows()

if len(objpoints) == 0:
    print("Erreur : aucun damier détecté dans aucune image.")
    exit()

ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
    objpoints, imgpoints, gray.shape[::-1], None, None)

print("Matrice intrinsèque :\n", camera_matrix)
print("Coefficients de distorsion :\n", dist_coeffs)
print("Rotation :\n", rvecs[0])
print("Translation :\n", tvecs[0])
