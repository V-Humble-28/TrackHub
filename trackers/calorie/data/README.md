# Indian Food Nutrition Dataset

## File
foods.csv

## Contents
The dataset includes food IDs, English and Hindi names, categories,
energy in kcal, protein, fat, carbohydrates, fibre, selected
micronutrients, and source information.

## Origin
Dataset repository:
https://github.com/prabhubng/indian-nutrition-data

The CSV includes a source column identifying the source listed
for each food record. Consult the original repository's README
and license for attribution and redistribution terms.

## Usage
The Tracker Hub calorie backend searches this local CSV file and
uses energy_kcal to calculate calories based on food weight.

Formula:
calories = weight_in_grams * energy_kcal_per_100g / 100

## Note
Nutrition values can vary by food variety and preparation method.
Choose the closest matching food entry.
