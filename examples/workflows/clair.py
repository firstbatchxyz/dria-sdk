from dria import DriaDataset, DatasetGenerator, Model
from dria.workflow.factory import Clair
import asyncio

# Create a dataset object with a name, description, and schema
my_dataset = DriaDataset(
    name="clair_test",  # Title of the dataset
    description="A test dataset",  # Brief description of the dataset
    schema=Clair.OutputSchema,  # Schema defining the expected structure of dataset entries
)

generator = DatasetGenerator(dataset=my_dataset)

# Provide a list of instructions to generate dataset entries
instructions = [
    {
        "task": "Math",
        "student_solution": "def factorial(n):\n    if n == 0:\n        return 1\n    else:\n        return n * factorial(n-1)",
    },
]

# Run the generator asynchronously to populate the dataset using the instructions and Clair schema
asyncio.run(
    generator.generate(
        instructions=instructions,  # The instructions for dataset generation
        workflows=Clair,  # Use Clair as the singleton schema and utility provider
        models=Model.GPT4O,  # Specify the model (e.g., GPT-4O) for generating outputs
    )
)

print(my_dataset.get_entries(data_only=True))
