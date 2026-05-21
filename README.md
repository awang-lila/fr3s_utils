# fr3s-utils
(Currently) small CLI commands to execute basic commands on FR3 Static 00, with the goal of building up to providing the infrastructure to hook advanced VLA-type policies into the robot.

## Configuration

Hosts, credentials, home joint pose, and timing defaults are read from `src/fr3s_utils/config.yaml` (bundled with the package).

## Running a Basic Robot Command

### Step 1: Un-Estop
Make Sure the E-Stop is Disengaged

### Step 2: Unlock Brakes
In this directory, ```uv run robot unlock```.

You should hear clicking from the arm as the brakes are unlocked. You might be asked to go up and push the buttons on the end effector. If this doesn't work, a safe bet is to e-stop and try again. If that doesn't work, power cycle the compute boxes and try again.

### Step 3: FCI From the GUI (TODO: automate)
The Python API command doesn't work for some reason. Someone should figure out why.

You can acccess the GUI with `https://left-box` or `https://right-box`.

### Step 4: Move Arm to Home
```
uv run move home --ip left-box # or right-box for the right arm.
```

### Step 5: Move the Arm Out and Back
See additional flags to specify how much to move the end effector, etc.
```
uv run move out-and-back --ip left-box # or right-box for the right arm.
```