# Installation

## Requirements and Setup

Dria SDK is compatible with Python 3.10 or higher. To install the SDK, simply run the following command in your terminal:

```bash
pip install dria
```

## Obtaining Your RPC Key

To interact with the Dria Network, you'll need an RPC (Remote Procedure Call) token. This token is essential for sending tasks to the network.
Visit the [Dria Login API](https://dkn.dria.co/auth/generate-token) and get your unique RPC token.

You can add your RPC key as an env variable by following command on your terminal
```bash
export DRIA_RPC_TOKEN=your-token-here
```

Alternatively, you can create a `.env` file and use `dotenv`
Your .env file should look like:
```dotenv
DRIA_RPC_TOKEN=your-token-here
```
Import env variables with:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Important Notes

- **Network Status**: The Dria Network is currently in __alpha__ stage. Access is managed through RPCs to ensure controlled access and trusted task execution.

- **Cost**: At present, there is no cost associated with generating data using Dria. However, a valid RPC token is required to access the network.

- **Contributing**: You can contribute to the Dria ecosystem by running a [node](https://dria.co/join) in the Dria network. This helps scale the network and improve throughput.

## Next Steps

Once you have your RPC token, you're ready to start using the Dria SDK. Check out the examples from cookbook (e.g. [Patient Dialogues](cookbook/patient_dialogues.md)) or see [Core Concepts](how-to/overview.md) to learn how to create your first synthetic data pipeline.