import cv2
import numpy as np

def draw_axis(img, camera_matrix, dist_coeffs, rvec, tvec, length=0.01):
    # Origine (coin du marqueur)
    origin = np.array([[0, 0, 0]], dtype=np.float32)
    # Points des axes X, Y, Z dans le repère du marqueur
    axis_points = np.array([[length, 0, 0],
                            [0, length, 0],
                            [0, 0, length]], dtype=np.float32)

    imgpts, _ = cv2.projectPoints(axis_points, rvec, tvec, camera_matrix, dist_coeffs)
    imgpts_origin, _ = cv2.projectPoints(origin, rvec, tvec, camera_matrix, dist_coeffs)

    corner = tuple(imgpts_origin.ravel().astype(int))
    x_axis = tuple(imgpts[0].ravel().astype(int))
    y_axis = tuple(imgpts[1].ravel().astype(int))
    z_axis = tuple(imgpts[2].ravel().astype(int))

    # Dessiner les 3 axes avec des couleurs différentes
    cv2.line(img, corner, x_axis, (0, 0, 255), 3)  # X en rouge
    cv2.line(img, corner, y_axis, (0, 255, 0), 3)  # Y en vert
    cv2.line(img, corner, z_axis, (255, 0, 0), 3)  # Z en bleu

# --- Code principal ---
camera_matrix = np.array([[873.35237059, 0., 687.97693455],
                          [0., 872.25271636, 362.30701839],
                          [0., 0., 1.]])
dist_coeffs = np.array([[-0.21794991, 0.61772464, 0.00099176, -0.00288021, -0.65518054]])

aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

try:
    parameters = cv2.aruco.DetectorParameters_create()
except AttributeError:
    parameters = cv2.aruco.DetectorParameters()

marker_length = 0.015

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Erreur : impossible d'ouvrir la webcam")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    corners, ids, rejected = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    if ids is not None:
        rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(corners, marker_length, camera_matrix, dist_coeffs)

        for i in range(len(ids)):
            cv2.aruco.drawDetectedMarkers(frame, corners)
            draw_axis(frame, camera_matrix, dist_coeffs, rvecs[i], tvecs[i], marker_length * 0.5)

            corner = corners[i][0]
            cv2.putText(frame, f"ID: {ids[i][0]}",
                        (int(corner[0][0]), int(corner[0][1]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    cv2.imshow("Test calibration live", frame)
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
