# Run the course simulations on a rented Vast.ai GPU computer

Use this when your own computer has no NVIDIA GPU (drones, Week 11; self-driving car, Week 10), or when you
simply do not want to run simulations on your own machine. You get the same browser desktop as on a laptop.
A suitable machine costs about **$0.10-0.20 per hour**; a three-hour lab costs well under $1.

## 1. Once: an account

1. Sign up at <https://cloud.vast.ai>, add a little credit (for example $5) under *Billing*.

## 2. Each lab: rent a machine with the course image

1. In the console open **Templates → New template** (or *Edit* a copy of any template) and fill in:

| Field | Mobile robot (Gazebo) | Drone (AirSim) | Self-driving car (CARLA) |
|---|---|---|---|
| Image path:tag | `abdulmannan617/tc70045e-ros2:humble` | `abdulmannan617/tc70045e-drone:latest` | `abdulmannan617/tc70045e-carla:latest` |
| Docker options | `-p 80:80 -e USER=ubuntu -e PASSWORD=choose-one -e RESOLUTION=1600x900` | same, plus `-p 41451:41451 -p 4570:4570` for HIL | same as mobile robot |
| Launch mode | **Docker ENTRYPOINT** | **Docker ENTRYPOINT** | **Docker ENTRYPOINT** |
| Disk | 40 GB | 80 GB | 80 GB |

   Choose your own `PASSWORD`: the desktop is reachable from the internet, and `PASSWORD` is its login.

2. **Search** with that template. Filter: 1 GPU, *GPU RAM* ≥ 8 GB (12 GB is comfortable for CARLA), *Disk* ≥ the
   value above, *Internet download* ≥ 500 Mb/s, a location near you (the desktop feels faster). Sort by price.
   Any RTX 3060 / 3070 / 4060 / 4070 / A4000 class GPU is enough. The mobile robot does not need a GPU, but GPU
   machines are often the cheapest anyway.
3. **Rent**. The first start downloads the image (15-30 GB): allow 10-30 minutes. Status turns *Running*.
   Still *Loading* after 30 minutes? Some machines download slowly (measured 7 Oct 2026: two of three hosts were
   still loading after 25 minutes). Destroy it and rent a different machine.
4. Click the instance's **IP / ports** button. Find the line `… -> 80/tcp` and open `http://<IP>:<that port>` in
   your browser. Log in with your password: this is the course desktop. The course code is at `~/labs`.

## 3. In the desktop

Open a terminal (*Applications → System Tools → Terminator*, or the icon on the desktop) and follow the week's
README, for example:

```bash
drone-sim start --world blocks                 # drone image
python3 ~/labs/examples/airsim/01_hello_airsim.py --show

carla-sim start --town Town04                  # CARLA image
python3 ~/labs/examples/carla/01_hello_carla.py
```

## 4. Keep your work, then DESTROY the instance

The machine is deleted with everything on it. Before you finish:

* **Copy your files out**: in the desktop, open Firefox and upload them to your OneDrive, or `git push` your work,
  or download them with `scp` (see below).
* Then **Destroy** the instance (bin icon). *Stop* is not enough: a stopped instance still costs money for its disk.

## 5. Command-line alternative (optional)

```bash
pip install vastai && vastai set api-key <your key from the console>
vastai search offers 'gpu_ram>=12 num_gpus=1 disk_space>=80 inet_down>=500 reliability>0.98' -o dph
vastai create instance <OFFER_ID> --image abdulmannan617/tc70045e-drone:latest --disk 80 \
    --env '-p 80:80 -p 41451:41451 -p 4570:4570 -e USER=ubuntu -e PASSWORD=choose-one -e RESOLUTION=1600x900' \
    --args
vastai show instance <INSTANCE_ID>          # wait for "running"; then the ports with: vastai show instance <ID> --raw
vastai destroy instance <INSTANCE_ID>
```

To copy files out with `scp` you need the SSH launch mode instead of *Docker ENTRYPOINT*; then start the desktop
yourself once, with `nohup bash /entrypoint.sh > /tmp/desktop.log 2>&1 &`.
