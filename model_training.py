from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
import pandas as pd
import joblib
import json

# Sample data

with open("model_data.json", "r", encoding="utf-8") as json_file:
    data = json.load(json_file)
# Create DataFrame
df = pd.DataFrame(data)

# Assuming you have a DataFrame 'df' with 'text' and 'label' columns
X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["label"], test_size=0.2, random_state=42
)

# TF-IDF Vectorization
vectorizer = TfidfVectorizer()
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# Support Vector Machine (SVM) classifier
classifier = SVC(kernel="linear")
classifier.fit(X_train_tfidf, y_train)

# Predictions
predictions = classifier.predict(X_test_tfidf)

# Evaluate the model
accuracy = accuracy_score(y_test, predictions)
print(f"Accuracy: {accuracy}")

# save model
# Save the trained vectorizer
joblib.dump(vectorizer, "tfidf_vectorizer.joblib")
joblib.dump(classifier, "svm_model.joblib")
