@echo off
title AI Crypto Advisor - Auto Update & Launch

echo 
echo 
echo


call venv\Scripts\activate

echo.
echo [1/4] 
python src/data_collection.py

echo.
echo [2/4] 🧠
python src/model_training.py

echo.
echo [3/4] 
python src/advisor_logic.py

echo.
echo [4/4] 
echo ==================================================

:: Dashboard Run
streamlit run main_dashboard.py

pause