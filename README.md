# ngram-recommender
* The script takes two corpora (`output_1.csv` and `output_2.csv` for the student model and `training.txt` for the teacher model [`output_1.csv` and `output_2.csv` are automatically combined]) of Java methods as input and automatically identifies the best-performing model based on a specific N-value. It then evaluates the selected model on the test set extracted from `output_*.csv`.
Since the training corpus differs from both the instructor-provided dataset and our own dataset, we store the results in a file named `results_[student/teacher]_model.json` to distinguish them accordingly.

# Installation:
1. Install [python 3.9+](https://www.python.org/downloads/) locally
2. Clone the repository to your workspace:  
```shell
~ $ git clone https://github.com/WhittJS/ngram-recommender.git
```
3. Navigate into the repository:
```shell
~ $ cd ngram-recommender
~/ngram-recommender $
```
4. Set up a virtual environment and activate it:
```shell
~/ngram-recommender $ python -m venv ./venv/
```
For macOS/Linux:
```shell 
~/ngram-recommender $ source venv/bin/activate
(venv) ~/ngram-recommender $ 
```
For Windows:
```shell
~\ngram-recommender $ .\venv\Scripts\activate.bat
(venv) ~\ngram-recommender $ 
```

5. To install the required packages: 
```shell
(venv) ~/ngram-recommender $ pip install -r requirements.txt
```
# Running the Program
1. Generate new JSON files based on `student_model.pkl` and `teacher_model.pkl`:
```shell
python ngram_recommender.py
```
2. To retrain either model, delete the file of the one you want to train and rerun the above command.
    * Edit the `min_ngram` and `max_ngram` values in the `train_test_model` function to train on ngrams within specified parameters.

# Report

The assignment report is available in the file Assignment_Report.pdf.
