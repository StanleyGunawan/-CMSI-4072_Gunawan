# Chess Learning Engine

This project is a chess engine and training setup built around a reinforcement learning agent. It includes a playable chess board UI, a training loop for the AI, and saved model checkpoints so training can be resumed later.

## What’s Included

- `main.py` starts the interactive chess board UI.
- `train.py` runs reinforcement learning training for the chess agent.
- `engine/` contains the board logic, AI, rendering, and training support.
- `chess_piece/` contains the piece movement rules.
- `resources/` stores the piece images used by the GUI.

## Requirements

The project is written in Python and uses `pygame` for the board UI and `torch` for the reinforcement learning model.

Install the dependencies you need before running the project. A typical setup is:

```bash
pip install pygame torch
```

## Running The Game UI

From the project root, run:

```bash
py main.py
```

This opens the chess board window and starts the interactive game interface.

## Running Training

Run training with the GUI enabled by default:

```bash
py train.py
```

Run training with no GUI:

```bash
py train.py -q
```

The `-q` flag is useful when you want faster headless training or are running on a machine where you do not want a window to open.

Run training for a specific number of episodes:

```bash
py train.py --episodes 1000
```

You can combine the flags if you want a headless run for a fixed number of episodes:

```bash
py train.py -q --episodes 1000
```

## Training Output

During training, the script can save and load model checkpoints such as:

- `chess_brain.pth`
- `chess_brain_best_eval.pth`

It also writes evaluation results to `eval_log.txt`.

## Notes

- Run the scripts from the project root so relative paths to `resources/` and model files resolve correctly.
- The GUI depends on the image files in `resources/`.
- If you want to inspect the training behavior, keep the GUI on; if you want a faster run, use `-q`.