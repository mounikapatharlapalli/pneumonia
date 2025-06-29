# -*- coding: utf-8 -*-
"""Pneumonia_Detection_using_CNN.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1SqdOBzbBqB_wxrICxTP_1mGUdnTKV2vv
"""

# IMPORTANT: RUN THIS CELL IN ORDER TO IMPORT YOUR KAGGLE DATA SOURCES,
# THEN FEEL FREE TO DELETE THIS CELL.
# NOTE: THIS NOTEBOOK ENVIRONMENT DIFFERS FROM KAGGLE'S PYTHON
# ENVIRONMENT SO THERE MAY BE MISSING LIBRARIES USED BY YOUR
# NOTEBOOK.
import kagglehub
paultimothymooney_chest_xray_pneumonia_path = kagglehub.dataset_download('paultimothymooney/chest-xray-pneumonia')

print('Data source import complete.')

"""# What is Pneumonia?
**Pneumonia is an inflammatory condition of the lung affecting primarily the small air sacs known as alveoli.Symptoms typically include some combination of productive or dry cough, chest pain, fever and difficulty breathing. The severity of the condition is variable. Pneumonia is usually caused by infection with viruses or bacteria and less commonly by other microorganisms, certain medications or conditions such as autoimmune diseases.Risk factors include cystic fibrosis, chronic obstructive pulmonary disease (COPD), asthma, diabetes, heart failure, a history of smoking, a poor ability to cough such as following a stroke and a weak immune system. Diagnosis is often based on symptoms and physical examination. Chest X-ray, blood tests, and culture of the sputum may help confirm the diagnosis.The disease may be classified by where it was acquired, such as community- or hospital-acquired or healthcare-associated pneumonia.**
![image.png](attachment:image.png)
"""

import kagglehub

# Download latest version
path = kagglehub.dataset_download("paultimothymooney/chest-xray-pneumonia")

print("Path to dataset files:", path)

# This Python 3 environment comes with many helpful analytics libraries installed
# It is defined by the kaggle/python docker image: https://github.com/kaggle/docker-python
# For example, here's several helpful packages to load in

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)

# Input data files are available in the "../input/" directory.
# For example, running this (by clicking run or pressing Shift+Enter) will list all files under the input directory

import os
for dirname, _, filenames in os.walk('/kaggle/input'):
    for filename in filenames:
        print(os.path.join(dirname, filename))

# Any results you write to the current directory are saved as output.

"""# Importing the necessary libraries"""

import matplotlib.pyplot as plt
import seaborn as sns
import keras
from keras.models import Sequential
from keras.layers import Dense, Conv2D , MaxPool2D , Flatten , Dropout , BatchNormalization
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report,confusion_matrix
from keras.callbacks import ReduceLROnPlateau
import cv2
import os

"""# Description of the Pneumonia Dataset
**The dataset is organized into 3 folders (train, test, val) and contains subfolders for each image category (Pneumonia/Normal). There are 5,863 X-Ray images (JPEG) and 2 categories (Pneumonia/Normal).
Chest X-ray images (anterior-posterior) were selected from retrospective cohorts of pediatric patients of one to five years old from Guangzhou Women and Children’s Medical Center, Guangzhou. All chest X-ray imaging was performed as part of patients’ routine clinical care.
For the analysis of chest x-ray images, all chest radiographs were initially screened for quality control by removing all low quality or unreadable scans. The diagnoses for the images were then graded by two expert physicians before being cleared for training the AI system. In order to account for any grading errors, the evaluation set was also checked by a third expert.**
"""

labels = ['PNEUMONIA', 'NORMAL']
img_size = 150
def get_training_data(data_dir):
    data = []
    for label in labels:
        path = os.path.join(data_dir, label)
        class_num = labels.index(label)
        for img in os.listdir(path):
            try:
                img_arr = cv2.imread(os.path.join(path, img), cv2.IMREAD_GRAYSCALE)
                resized_arr = cv2.resize(img_arr, (img_size, img_size)) # Reshaping images to preferred size
                data.append([resized_arr, class_num])
            except Exception as e:
                print(e)
    return np.array(data)

"""# Loading the Dataset"""

from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Define paths
train_path = "/root/.cache/kagglehub/datasets/paultimothymooney/chest-xray-pneumonia/versions/2/chest_xray/chest_xray/train"
val_path = "/root/.cache/kagglehub/datasets/paultimothymooney/chest-xray-pneumonia/versions/2/chest_xray/chest_xray/val"
test_path = "/root/.cache/kagglehub/datasets/paultimothymooney/chest-xray-pneumonia/versions/2/chest_xray/chest_xray/test"

# Data augmentation and normalization
datagen = ImageDataGenerator(rescale=1./255)

# Load training data
train = datagen.flow_from_directory(
    train_path,
    target_size=(150, 150),  # Resize images to match model input size
    batch_size=32,
    class_mode='binary'  # 'binary' since it's a two-class problem
)

# Load validation data
val = datagen.flow_from_directory(
    val_path,
    target_size=(150, 150),
    batch_size=32,
    class_mode='binary'
)

# Load test data
test = datagen.flow_from_directory(
    test_path,
    target_size=(150, 150),
    batch_size=32,
    class_mode='binary',
    shuffle=False  # Don't shuffle test data for evaluation
)

"""# Data Visualization & Preprocessing"""

import seaborn as sns
import matplotlib.pyplot as plt

l = []
for images, labels in train:  # Unpacking the batch
    for label in labels:  # Iterating over the batch of labels
        if label == 0:
            l.append("Pneumonia")
        else:
            l.append("Normal")

# Plot the distribution
sns.set_style('darkgrid')
sns.countplot(x=l)
plt.xlabel("Class")
plt.ylabel("Count")
plt.title("Distribution of Pneumonia and Normal Cases")
plt.show()

"""**The data seems imbalanced . To increase the no. of training examples, we will use data augmentation**

**Previewing the images of both the classes**
"""

plt.figure(figsize = (5,5))
plt.imshow(train[0][0], cmap='gray')
plt.title(labels[train[0][1]])

plt.figure(figsize = (5,5))
plt.imshow(train[-1][0], cmap='gray')
plt.title(labels[train[-1][1]])

# Use train, test, and val generators directly without loading everything into memory
train_generator = train  # Uses the ImageDataGenerator instance
val_generator = val
test_generator = test

x_train = []
y_train = []

x_val = []
y_val = []

x_test = []
y_test = []

for feature, label in train:
    x_train.append(feature)
    y_train.append(label)

for feature, label in test:
    x_test.append(feature)
    y_test.append(label)

for feature, label in val:
    x_val.append(feature)
    y_val.append(label)

"""**We perform a grayscale normalization to reduce the effect of illumination's differences.Moreover the CNN converges faster on [0..1] data than on [0..255].**"""

# Normalize the data
x_train = np.array(x_train) / 255
x_val = np.array(x_val) / 255
x_test = np.array(x_test) / 255

# resize data for deep learning
x_train = x_train.reshape(-1, img_size, img_size, 1)
y_train = np.array(y_train)

x_val = x_val.reshape(-1, img_size, img_size, 1)
y_val = np.array(y_val)

x_test = x_test.reshape(-1, img_size, img_size, 1)
y_test = np.array(y_test)

"""# Data Augmentation
**In order to avoid overfitting problem, we need to expand artificially our dataset. We can make your existing dataset even larger. The idea is to alter the training data with small transformations to reproduce the variations.
Approaches that alter the training data in ways that change the array representation while keeping the label the same are known as data augmentation techniques. Some popular augmentations people use are grayscales, horizontal flips, vertical flips, random crops, color jitters, translations, rotations, and much more.
By applying just a couple of these transformations to our training data, we can easily double or triple the number of training examples and create a very robust model.**
"""

from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Define paths
train_path = "/root/.cache/kagglehub/datasets/paultimothymooney/chest-xray-pneumonia/versions/2/chest_xray/chest_xray/train"
val_path = "/root/.cache/kagglehub/datasets/paultimothymooney/chest-xray-pneumonia/versions/2/chest_xray/chest_xray/val"
test_path = "/root/.cache/kagglehub/datasets/paultimothymooney/chest-xray-pneumonia/versions/2/chest_xray/chest_xray/test"

# Create ImageDataGenerator with augmentation for training
datagen = ImageDataGenerator(
    rescale=1./255,  # Normalize pixel values
    rotation_range=30,
    zoom_range=0.2,
    width_shift_range=0.1,
    height_shift_range=0.1,
    horizontal_flip=True
)

# No augmentation for validation & test sets, only rescaling
test_val_datagen = ImageDataGenerator(rescale=1./255)

# Load training data with augmentation
train_generator = datagen.flow_from_directory(
    train_path,
    target_size=(150, 150),
    batch_size=32,
    class_mode='binary',
    color_mode='grayscale'  # ✅ Ensures images are single-channel
)

# Load validation data
val_generator = test_val_datagen.flow_from_directory(
    val_path,
    target_size=(150, 150),
    batch_size=32,
    class_mode='binary',
    color_mode='grayscale'  # ✅ Ensures images are single-channel
)

# Load test data
test_generator = test_val_datagen.flow_from_directory(
    test_path,
    target_size=(150, 150),
    batch_size=32,
    class_mode='binary',
    color_mode='grayscale',  # ✅ Ensures images are single-channel
    shuffle=False
)

"""For the data augmentation, i choosed to :
1. Randomly rotate some training images by 30 degrees
2. Randomly Zoom by 20% some training images
3. Randomly shift images horizontally by 10% of the width
4. Randomly shift images vertically by 10% of the height
5. Randomly flip images horizontally.
Once our model is ready, we fit the training dataset.

# Training the Model
"""

model = Sequential()
model.add(Conv2D(32 , (3,3) , strides = 1 , padding = 'same' , activation = 'relu' , input_shape = (150,150,1)))
model.add(BatchNormalization())
model.add(MaxPool2D((2,2) , strides = 2 , padding = 'same'))
model.add(Conv2D(64 , (3,3) , strides = 1 , padding = 'same' , activation = 'relu'))
model.add(Dropout(0.1))
model.add(BatchNormalization())
model.add(MaxPool2D((2,2) , strides = 2 , padding = 'same'))
model.add(Conv2D(64 , (3,3) , strides = 1 , padding = 'same' , activation = 'relu'))
model.add(BatchNormalization())
model.add(MaxPool2D((2,2) , strides = 2 , padding = 'same'))
model.add(Conv2D(128 , (3,3) , strides = 1 , padding = 'same' , activation = 'relu'))
model.add(Dropout(0.2))
model.add(BatchNormalization())
model.add(MaxPool2D((2,2) , strides = 2 , padding = 'same'))
model.add(Conv2D(256 , (3,3) , strides = 1 , padding = 'same' , activation = 'relu'))
model.add(Dropout(0.2))
model.add(BatchNormalization())
model.add(MaxPool2D((2,2) , strides = 2 , padding = 'same'))
model.add(Flatten())
model.add(Dense(units = 128 , activation = 'relu'))
model.add(Dropout(0.2))
model.add(Dense(units = 1 , activation = 'sigmoid'))
model.compile(optimizer = "rmsprop" , loss = 'binary_crossentropy' , metrics = ['accuracy'])
model.summary()

learning_rate_reduction = ReduceLROnPlateau(monitor='val_accuracy', patience = 2, verbose=1,factor=0.3, min_lr=0.000001)

history = model.fit(
    train_generator,  # Use generator instead of raw data
    epochs=12,
    validation_data=val_generator,
    callbacks=[learning_rate_reduction]  # Ensure this is defined
)

print("Loss of the model is - " , model.evaluate(x_test,y_test)[0])
print("Accuracy of the model is - " , model.evaluate(x_test,y_test)[1]*100 , "%")

"""# Analysis after Model Training"""

epochs = [i for i in range(12)]
fig , ax = plt.subplots(1,2)
train_acc = history.history['accuracy']
train_loss = history.history['loss']
val_acc = history.history['val_accuracy']
val_loss = history.history['val_loss']
fig.set_size_inches(20,10)

ax[0].plot(epochs , train_acc , 'go-' , label = 'Training Accuracy')
ax[0].plot(epochs , val_acc , 'ro-' , label = 'Validation Accuracy')
ax[0].set_title('Training & Validation Accuracy')
ax[0].legend()
ax[0].set_xlabel("Epochs")
ax[0].set_ylabel("Accuracy")

ax[1].plot(epochs , train_loss , 'g-o' , label = 'Training Loss')
ax[1].plot(epochs , val_loss , 'r-o' , label = 'Validation Loss')
ax[1].set_title('Testing Accuracy & Loss')
ax[1].legend()
ax[1].set_xlabel("Epochs")
ax[1].set_ylabel("Training & Validation Loss")
plt.show()

import numpy as np

# Get predictions from the model
predictions = model.predict(test_generator)

# Convert probabilities to class labels (0 or 1)
predictions = np.argmax(predictions, axis=1)

# Display the first 15 predictions
print(predictions[::])

from sklearn.metrics import classification_report
import numpy as np

# Get true labels from test_generator
y_test = test_generator.classes  # ✅ Extracts true labels

# Get predictions
predictions = model.predict(test_generator)

# Convert probabilities to class labels
predictions = (predictions > 0.5).astype(int).flatten()  # ✅ Ensure it's a 1D array

# Print classification report
print(classification_report(y_test, predictions, target_names=['Pneumonia (Class 0)', 'Normal (Class 1)']))

from sklearn.metrics import confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

# Compute confusion matrix
cm = confusion_matrix(y_test, predictions)

# Plot confusion matrix
plt.figure(figsize=(6,4))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Pneumonia (Class 0)', 'Normal (Class 1)'], yticklabels=['Pneumonia (Class 0)', 'Normal (Class 1)'])
plt.xlabel('Predicted Label')
plt.ylabel('True Label')
plt.title('Confusion Matrix')
plt.show()

import pandas as pd
from sklearn.metrics import confusion_matrix

# Compute confusion matrix
cm = confusion_matrix(y_test, predictions)

# Convert to DataFrame with proper labels
cm_df = pd.DataFrame(cm, index=['Actual Pneumonia (0)', 'Actual Normal (1)'],
                          columns=['Predicted Pneumonia (0)', 'Predicted Normal (1)'])

# Display the confusion matrix
print(cm_df)

import seaborn as sns
import matplotlib.pyplot as plt

# Define class labels
labels = ['Pneumonia (Class 0)', 'Normal (Class 1)']

# Plot the heatmap
plt.figure(figsize=(8,6))  # Adjusted figure size for better readability
sns.heatmap(cm_df, cmap="Blues", linecolor='black', linewidth=1, annot=True, fmt='d',
            xticklabels=labels, yticklabels=labels)

# Title and labels
plt.title("Confusion Matrix", fontsize=14)
plt.xlabel("Predicted Label", fontsize=12)
plt.ylabel("Actual Label", fontsize=12)
plt.show()

import numpy as np

# Ensure y_test is a NumPy array
y_test = np.array(y_test)

# Get indices of correctly and incorrectly classified samples
correct = np.where(predictions == y_test)[0]
incorrect = np.where(predictions != y_test)[0]

print(f"Correctly classified samples: {len(correct)}")
print(f"Incorrectly classified samples: {len(incorrect)}")

"""**Some of the Correctly Predicted Classes**"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from tensorflow.keras.models import load_model
from sklearn.metrics import classification_report, confusion_matrix

# Load test data (first batch)
x_test, y_test = next(test_generator)

# Make predictions
predictions = np.argmax(model.predict(x_test), axis=1)

# Class Labels
class_labels = ["Pneumonia", "Normal"]

# ✅ Confusion Matrix Fix: Ensure it always has shape (2,2)
cm = confusion_matrix(y_test, predictions, labels=[0, 1])
cm_df = pd.DataFrame(cm, index=class_labels, columns=class_labels)

# Plot Confusion Matrix
plt.figure(figsize=(6, 6))
sns.heatmap(cm_df, cmap="Blues", annot=True, fmt="d", linewidths=1, linecolor="black")
plt.xlabel("Predicted Label")
plt.ylabel("Actual Label")
plt.title("Confusion Matrix")
plt.show()

# ✅ Display Images with Actual & Predicted Labels
plt.figure(figsize=(10, 10))
for i in range(6):  # Show first 6 images
    plt.subplot(3, 2, i + 1)
    plt.xticks([])
    plt.yticks([])
    plt.imshow(x_test[i].squeeze(), cmap="gray")

    actual = class_labels[int(y_test[i])]
    predicted = class_labels[int(predictions[i])]

    plt.title(f"Pred: {predicted} | Actual: {actual}", fontsize=12, color='green' if actual == predicted else 'red')

plt.tight_layout()
plt.show()

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from tensorflow.keras.models import load_model
from sklearn.metrics import classification_report, confusion_matrix

# Load test data (batch of 32 images from test_generator)
x_test, y_test = next(test_generator)

# Make predictions
predictions = np.argmax(model.predict(x_test), axis=1)

# Class Labels
class_labels = ["Pneumonia", "Normal"]

# ✅ Confusion Matrix Fix: Ensure it always has shape (2,2)
cm = confusion_matrix(y_test, predictions, labels=[0, 1])
cm_df = pd.DataFrame(cm, index=class_labels, columns=class_labels)

# Plot Confusion Matrix
plt.figure(figsize=(6, 6))
sns.heatmap(cm_df, cmap="Blues", annot=True, fmt="d", linewidths=1, linecolor="black")
plt.xlabel("Predicted Label")
plt.ylabel("Actual Label")
plt.title("Confusion Matrix")
plt.show()

# ✅ Separate correctly classified Pneumonia & Normal images
pneumonia_imgs = [i for i in range(len(y_test)) if y_test[i] == 0]  # Pneumonia
normal_imgs = [i for i in range(len(y_test)) if y_test[i] == 1]  # Normal

# ✅ Display 3 Pneumonia cases
plt.figure(figsize=(10, 5))
for i, idx in enumerate(pneumonia_imgs[:3]):
    plt.subplot(1, 3, i + 1)
    plt.xticks([])
    plt.yticks([])
    plt.imshow(x_test[idx].squeeze(), cmap="gray")

    actual = class_labels[int(y_test[idx])]
    predicted = class_labels[int(predictions[idx])]

    plt.title(f"Pred: {predicted} | Actual: {actual}", fontsize=10, color='green' if actual == predicted else 'red')

plt.suptitle("Pneumonia Cases", fontsize=14)
plt.tight_layout()
plt.show()

# ✅ Display 3 Normal cases
plt.figure(figsize=(10, 5))
for i, idx in enumerate(normal_imgs[:3]):
    plt.subplot(1, 3, i + 1)
    plt.xticks([])
    plt.yticks([])
    plt.imshow(x_test[idx].squeeze(), cmap="gray")

    actual = class_labels[int(y_test[idx])]
    predicted = class_labels[int(predictions[idx])]

    plt.title(f"Pred: {predicted} | Actual: {actual}", fontsize=10, color='green' if actual == predicted else 'red')

plt.suptitle("Normal Cases", fontsize=14)
plt.tight_layout()
plt.show()

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from tensorflow.keras.models import load_model
from sklearn.metrics import classification_report, confusion_matrix

# Load test data (first 1000 images from test_generator)
x_test, y_test = [], []

# Extract 1000 images batch by batch from the test generator
for _ in range(32):  # Assuming batch size = 32, 32 * 32 ≈ 1000 images
    x_batch, y_batch = next(test_generator)
    x_test.append(x_batch)
    y_test.append(y_batch)

# Convert list to numpy arrays
x_test = np.concatenate(x_test, axis=0)[:1000]  # First 1000 images
y_test = np.concatenate(y_test, axis=0)[:1000]

# Make predictions
predictions = np.argmax(model.predict(x_test), axis=1)

# Class Labels
class_labels = ["Pneumonia", "Normal"]

# ✅ Confusion Matrix Fix: Ensure it always has shape (2,2)
cm = confusion_matrix(y_test, predictions, labels=[0, 1])
cm_df = pd.DataFrame(cm, index=class_labels, columns=class_labels)

# Plot Confusion Matrix
plt.figure(figsize=(6, 6))
sns.heatmap(cm_df, cmap="Blues", annot=True, fmt="d", linewidths=1, linecolor="black")
plt.xlabel("Predicted Label")
plt.ylabel("Actual Label")
plt.title("Confusion Matrix")
plt.show()

# ✅ Display First 1000 Test Images with Predictions
plt.figure(figsize=(20, 200))

for i in range(1000):
    plt.subplot(50, 20, i + 1)  # 50 rows, 20 columns
    plt.xticks([])
    plt.yticks([])
    plt.imshow(x_test[i].squeeze(), cmap="gray")  # Display image

    actual = class_labels[int(y_test[i])]
    predicted = class_labels[int(predictions[i])]

    # Green if correct, Red if incorrect
    color = "green" if actual == predicted else "red"

    plt.title(f"Pred: {predicted}\nActual: {actual}", fontsize=6, color=color)

plt.suptitle("First 1000 Test Images with Predictions", fontsize=16)
plt.tight_layout()
plt.show()

import matplotlib.pyplot as plt
import numpy as np

# Set up the figure size
plt.figure(figsize=(20, 20))

# Loop through the first 100 test images
for i in range(100):
    plt.subplot(10, 10, i + 1)  # Create a 10x10 grid of subplots
    plt.xticks([])  # Remove x-axis ticks
    plt.yticks([])  # Remove y-axis ticks

    # Display the image (assuming grayscale images)
    plt.imshow(x_test[i].squeeze(), cmap="gray", interpolation="none")

    # Set title with Predicted and Actual labels
    plt.title(f"P:{predictions[i]} | A:{y_test[i]}", fontsize=10, color='blue')

plt.tight_layout()  # Adjust spacing between images
plt.show()  # Show the plot

