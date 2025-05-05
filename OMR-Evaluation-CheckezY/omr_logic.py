# omr_logic.py

import cv2
import numpy as np
import utlis

def evaluate_omr(image_path, ans):  # Accepts image_path and ans as arguments
    heightImg = 700
    widthImg = 700
    questions = len(ans)
    choices = 5

    img = cv2.imread(image_path)
    img = cv2.resize(img, (widthImg, heightImg))
    imgFinal = img.copy()
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)
    imgCanny = cv2.Canny(imgBlur, 10, 70)

    contours, hierarchy = cv2.findContours(imgCanny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    rectCon = utlis.rectContour(contours)
    if len(rectCon) < 2:
        return img, 0  # Fallback if detection fails

    biggestPoints = utlis.getCornerPoints(rectCon[0])
    gradePoints = utlis.getCornerPoints(rectCon[1])

    if biggestPoints.size != 0 and gradePoints.size != 0:
        biggestPoints = utlis.reorder(biggestPoints)
        pts1 = np.float32(biggestPoints)
        pts2 = np.float32([[0, 0], [widthImg, 0], [0, heightImg], [widthImg, heightImg]])
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        imgWarpColored = cv2.warpPerspective(img, matrix, (widthImg, heightImg))

        gradePoints = utlis.reorder(gradePoints)
        ptsG1 = np.float32(gradePoints)
        ptsG2 = np.float32([[0, 0], [325, 0], [0, 150], [325, 150]])
        matrixG = cv2.getPerspectiveTransform(ptsG1, ptsG2)
        imgGradeDisplay = cv2.warpPerspective(img, matrixG, (325, 150))

        imgWarpGray = cv2.cvtColor(imgWarpColored, cv2.COLOR_BGR2GRAY)
        imgThresh = cv2.threshold(imgWarpGray, 170, 255, cv2.THRESH_BINARY_INV)[1]

        boxes = utlis.splitBoxes(imgThresh)
        myPixelVal = np.zeros((questions, choices))
        countR = 0
        countC = 0
        for image in boxes:
            totalPixels = cv2.countNonZero(image)
            myPixelVal[countR][countC] = totalPixels
            countC += 1
            if countC == choices:
                countC = 0
                countR += 1

        myIndex = []
        for row in myPixelVal:
            max_val = np.max(row)
            candidates = np.where(row >= max_val * 0.9)[0]  # Accept within 90% of max
            if len(candidates) == 1:
                myIndex.append(candidates[0])
            else:
                myIndex.append(-1)  # Ambiguous or no clear answer

        grading = [1 if myIndex[i] == ans[i] else 0 for i in range(len(ans)) if myIndex[i] != -1]
        score = int((sum(grading) / questions) * 100)

        utlis.showAnswers(imgWarpColored, myIndex, grading, ans)
        imgRawDrawings = np.zeros_like(imgWarpColored)
        utlis.showAnswers(imgRawDrawings, myIndex, grading, ans)
        invMatrix = cv2.getPerspectiveTransform(pts2, pts1)
        imgInvWarp = cv2.warpPerspective(imgRawDrawings, invMatrix, (widthImg, heightImg))

        imgRawGrade = np.zeros_like(imgGradeDisplay, np.uint8)
        cv2.putText(imgRawGrade, str(score) + "%", (70, 100), cv2.FONT_HERSHEY_COMPLEX, 3, (0, 255, 255), 3)
        invMatrixG = cv2.getPerspectiveTransform(ptsG2, ptsG1)
        imgInvGradeDisplay = cv2.warpPerspective(imgRawGrade, invMatrixG, (widthImg, heightImg))

        imgFinal = cv2.addWeighted(imgFinal, 1, imgInvWarp, 1, 0)
        imgFinal = cv2.addWeighted(imgFinal, 1, imgInvGradeDisplay, 1, 0)

    return imgFinal, score
