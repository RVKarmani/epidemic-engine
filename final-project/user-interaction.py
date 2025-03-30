import pathlib

ML_MODEL_PATH = "./ml-model"
# COMMAND = "docker compose exec spark-master spark-submit --master spark://spark-master:7077 ml-model/model-sample.py "
FLAGS = []

def promptUserReturnSelection(prompt, options):
    while True:
        for i in range(len(options)):
            print(f"{i+1}. {options[i]}")
        choice = input(f"{prompt}: ")
        try:
            choice = int(choice)
            if 1 <= choice <= len(options):
                return options[choice - 1]
            else:
                print("Wrong option selected, please try again")
        except ValueError:
            print("Please enter a valid number.")

KAFKA_CHOICE = "Kafka"
DATASET_CHOICE = "CSV dataset"
print("\nWhat kind of dataset are you working with?")
choice = promptUserReturnSelection("Please enter number", [DATASET_CHOICE, KAFKA_CHOICE])

if choice == DATASET_CHOICE:
    print("\nSelect input file to run prediction on")
    input_file = promptUserReturnSelection("Select file", [f.name for f in pathlib.Path().glob(f"{ML_MODEL_PATH}/inputs/*.csv")])
    FLAGS.append(f"--input-file {input_file}")

elif choice == KAFKA_CHOICE:
    print("Kafka data used")
    # Add prompt for Kafka starting offset
    offset_choice = promptUserReturnSelection("Choose the Kafka offset position", ["earliest", "latest"])
    FLAGS.append(f"--mode {KAFKA_CHOICE}")
    FLAGS.append(f"--starting-offsets {offset_choice}")

print("\nSelect model used to predict with")
model_name = promptUserReturnSelection("Select model", [f.name for f in pathlib.Path().glob(f"{ML_MODEL_PATH}/saved-models/*")])
FLAGS.append(f"--model-name {model_name}")

if model_name == "anomaly_detection_model":
    COMMAND = "docker compose exec spark-master spark-submit --master spark://spark-master:7077 ml-model/anomaly-detection-model.py "
elif model_name == "risk_prediction_model":
    COMMAND = "docker compose exec spark-master spark-submit --master spark://spark-master:7077 ml-model/risk-prediction-model.py "

print("\nRun the following command in your terminal in the final-project folder to run your job....\n")
COLOR_GREEN = "\033[0;32m"
END_COLOUR="\033[0m"

FINAL_CMD = COMMAND + ' '.join(FLAGS)
print(f"{COLOR_GREEN}{FINAL_CMD}{END_COLOUR}")
