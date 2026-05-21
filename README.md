# fr3s-utils
(Currently) small CLI commands to execute basic commands on FR3 Static 00, with the goal of building up to providing the infrastructure to hook advanced VLA-type policies into the robot.

## Configuration

Hosts, credentials, home joint pose, and timing defaults are read from `src/fr3s_utils/config.yaml` (bundled with the package).

## Running a Basic Robot Command

### Step 1: Un-Estop
Make Sure the E-Stop(s) are Disengaged

### Step 2: Unlock Brakes
In this directory, ```uv run robot unlock```.

You should hear clicking from the arm as the brakes are unlocked. You might be asked to go up and push the buttons on the end effector. If this doesn't work, a safe bet is to e-stop and try again. If that doesn't work, power cycle the compute boxes and try again.

### Step 3: FCI From the GUI (TODO: automate)
The Python API command doesn't work for some reason. Someone should figure out why.

You can acccess the GUI with `https://left-box` and `https://right-box`.

Click "Activate FCI" on the drop-down on the right.

![alt text](image.png)

### Step 4: Move Arm to Home
```
uv run move home --ip left-box # or right-box for the right arm.
```

### Step 5: Move the Arm Out and Back
See additional flags to specify how much to move the end effector, etc.
```
uv run move out-and-back --ip left-box # or right-box for the right arm.
```

It should print out the error between the commanded move amount and the measured move amount.

```
lab@OAP103-Ser9-NUC:~/repos/fr3s_utils$ uv run move out-and-back --ip left-box
Out segment:
  Commanded Δxyz (m):     [-0.1  0.   0. ]
  Estimated Δxyz (m):    [-0.070149 -0.070609  0.008509]
  Error (est - cmd) (m): [ 0.029851 -0.070609  0.008509]
  ‖Error‖₂ (m):         0.077130
Back segment:
  Commanded Δxyz (m):     [ 0.1 -0.  -0. ]
  Estimated Δxyz (m):    [ 0.070167  0.070713 -0.008417]
  Error (est - cmd) (m): [-0.029833  0.070713 -0.008417]
  ‖Error‖₂ (m):         0.077209
```