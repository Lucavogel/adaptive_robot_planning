import cv2
import cv2.aruco as aruco
import numpy as np

def estimate_marker_pose(corners, marker_length, camera_matrix, dist_coeffs):
    """
    Estime la pose d'un marqueur ArUco avec solvePnP.

    Args:
        corners (np.ndarray): Tableau (4, 2) des coins du marqueur détecté dans l'image.
        marker_length (float): Longueur du côté du marqueur (en mètres).
        camera_matrix (np.ndarray): Matrice de calibration de la caméra.
        dist_coeffs (np.ndarray): Coefficients de distorsion de la caméra.

    Returns:
        (rvec, tvec): Vecteurs de rotation et de translation, ou (None, None) si échec.
    """
    # Coins du marqueur dans le référentiel monde
    obj_points = np.array([
        [-marker_length / 2, marker_length / 2, 0],
        [marker_length / 2, marker_length / 2, 0],
        [marker_length / 2, -marker_length / 2, 0],
        [-marker_length / 2, -marker_length / 2, 0]
    ], dtype=np.float32)

    # reshape au cas où
    img_points = corners.reshape(-1, 2).astype(np.float32)

    success, rvec, tvec = cv2.solvePnP(obj_points, img_points, camera_matrix, dist_coeffs)

    if success:
        return rvec, tvec
    else:
        return None, None


print("OpenCV version:", cv2.__version__)

cap = cv2.VideoCapture(0)

camera_matrix = np.array([[873.35237059, 0., 687.97693455],
                          [0., 872.25271636, 362.30701839],
                          [0., 0., 1.]])
dist_coeffs = np.array([[-0.21794991, 0.61772464, 0.00099176, -0.00288021, -0.65518054]])

marker_length = 0.04  # en mètres

aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, parameters)

# Points 3D du carré ArUco (en coord. monde)
# Dans l'ordre : coin en haut à gauche, en haut à droite, en bas à droite, en bas à gauche
obj_points = np.array([
    [-marker_length / 2, marker_length / 2, 0],
    [marker_length / 2, marker_length / 2, 0],
    [marker_length / 2, -marker_length / 2, 0],
    [-marker_length / 2, -marker_length / 2, 0]
], dtype=np.float32)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, rejected = detector.detectMarkers(gray)

    if ids is not None:
        aruco.drawDetectedMarkers(frame, corners, ids)

        for i in range(len(ids)):
            img_points = corners[i][0]  # coins du marqueur dans l'image
            success, rvec, tvec = cv2.solvePnP(obj_points, img_points, camera_matrix, dist_coeffs)

            if success:
                cv2.drawFrameAxes(frame, camera_matrix, dist_coeffs, rvec, tvec, 0.03)
                print(f"ID: {ids[i][0]} - Position: x={tvec[0][0]:.3f} m, y={tvec[1][0]:.3f} m, z={tvec[2][0]:.3f} m")

    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
