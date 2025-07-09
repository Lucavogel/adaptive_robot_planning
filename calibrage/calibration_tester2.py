import cv2
import numpy as np

# Supposons que tu as déjà obtenu ta calibration :
# camera_matrix, dist_coeffs, rvecs, tvecs par cv2.calibrateCamera
# Pour l'exemple, on prend des valeurs fictives (remplace-les par les tiennes) :
camera_matrix = np.array([[873.35237059, 0., 687.97693455],
                          [0., 872.25271636, 362.30701839],
                          [0., 0., 1.]])
dist_coeffs = np.array([[-0.21794991, 0.61772464, 0.00099176, -0.00288021, -0.65518054]])

# Charger une image prise par ta caméra (non corrigée)
img = cv2.imread('/home/luca/Documents/GitHub/adaptive_robot_planning/calibrage/calibrage_image/2025-07-04-183915.jpg')  # adapte ce chemin

# Correction (undistort)
h, w = img.shape[:2]
new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(camera_matrix, dist_coeffs, (w,h), 1, (w,h))

img_undistorted = cv2.undistort(img, camera_matrix, dist_coeffs, None, new_camera_matrix)

# Découper l'image corrigée selon roi (zone utile)
x, y, w, h = roi
img_undistorted = img_undistorted[y:y+h, x:x+w]

# Afficher les deux images côte à côte pour comparaison
cv2.imshow("Originale", img)
cv2.imshow("Corrigée (undistort)", img_undistorted)
cv2.waitKey(0)
cv2.destroyAllWindows()
