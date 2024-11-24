#!/usr/bin/env python3
import rospy
from gazebo_msgs.srv import SpawnModel, DeleteModel, SetModelState, GetModelState, GetWorldProperties
from gazebo_msgs.msg import ModelState
from geometry_msgs.msg import Pose
import os
import threading
import math
import time
from tf.transformations import quaternion_from_euler, euler_from_quaternion
from time import sleep
from problem_solver import X


BLOCK_WIDTH = 1
BLOCK_HEIGHT = 1  # Corrected the spelling from 'HIGHT' to 'HEIGHT'


def delete_all_models():
    # Wait for Gazebo services to be available
    rospy.wait_for_service('/gazebo/get_world_properties')
    rospy.wait_for_service('/gazebo/delete_model')

    try:
        # Create service clients
        get_world_properties = rospy.ServiceProxy('/gazebo/get_world_properties', GetWorldProperties)
        delete_model = rospy.ServiceProxy('/gazebo/delete_model', DeleteModel)

        # Get list of all models in the Gazebo world
        world_properties = get_world_properties()
        model_names = world_properties.model_names

        # Iterate over all model names and delete each one
        for model_name in model_names:
            try:
                delete_model(model_name)
            except rospy.ServiceException:
                pass

    except rospy.ServiceException:
        pass


def location_to_coordinates(loc):
    # Assuming loc is of the form 'loc(x,y)'
    loc_str = str(loc)
    if loc_str.startswith('loc(') and loc_str.endswith(')'):
        coords = loc_str[4:-1]  # Extract 'x,y' from 'loc(x,y)'
        x_str, y_str = coords.split(',')
        x = int(x_str.strip())
        y = int(y_str.strip())
        return x, y
    else:
        raise ValueError("Invalid location format: {}".format(loc_str))


class SimulationManager:
    def __init__(self, world_map: list, t_locs, p_locs, p_dest, actions):
        self.world_map = world_map
        self.t_locs = t_locs
        self.p_locs = p_locs
        self.p_dest = p_dest
        self.actions = actions

        rospy.init_node('simulation_manager', anonymous=True)

        # Wait for ROS services before proceeding
        rospy.wait_for_service('/gazebo/spawn_sdf_model')
        rospy.wait_for_service('/gazebo/delete_model')
        rospy.wait_for_service('/gazebo/set_model_state')
        rospy.wait_for_service('/gazebo/get_world_properties')
        rospy.wait_for_service('/gazebo/get_model_state')

        # Create service proxies
        self.spawn_model = rospy.ServiceProxy('/gazebo/spawn_sdf_model', SpawnModel)
        self.delete_model = rospy.ServiceProxy('/gazebo/delete_model', DeleteModel)
        self.set_model_state = rospy.ServiceProxy('/gazebo/set_model_state', SetModelState)
        self.get_model_state_service = rospy.ServiceProxy('/gazebo/get_model_state', GetModelState)

        # Mapping of passengers attached to taxis
        self.passenger_taxi_mapping = {}

        self.init()

    def init(self):
        delete_all_models()
        # Dictionaries to keep track of objects
        self.taxis = {}
        self.passengers = {}
        self.blocks = {}

        # Add boundary blocks
        for i in range(len(self.world_map)):
            self.spawn_block((i, -1))
            self.spawn_block((i, len(self.world_map[0])))

        for i in range(-1, 1 + len(self.world_map[0])):
            self.spawn_block((-1, i))
            self.spawn_block((len(self.world_map), i))

        for i, row in enumerate(self.world_map):
            for j, tile in enumerate(row):
                if tile == X:
                    self.spawn_block((i, j))

        for loc in self.t_locs:
            self.spawn_taxi(loc)

        for loc in self.p_locs:
            self.spawn_passenger(loc)

    def action_callback(self, action_array, threaded=False):
        if not threaded:
            self.handle_action(action_array[0])
            return
        threads = []
        for action in action_array:
            thr = threading.Thread(target=self.handle_action, args=(action,))
            thr.start()
            threads.append(thr)

        for thr in threads:
            thr.join()

    def spawn_block(self, block):
        model_name = 'block_{0}'.format(len(self.blocks))

        model_xml = """
        <?xml version="1.0" ?>
        <sdf version="1.6">
            <model name="{0}">
                <static>true</static>
                <link name="link">

                <gravity>false</gravity> <!-- Disable gravity -->

                    <visual name="visual">
                        <geometry>
                            <box>
                                <size>{1} {2} 1.0</size>
                            </box>
                        </geometry>
                        <material>
                            <ambient>0.5 0.5 0.5 1</ambient>
                            <diffuse>0.5 0.5 0.5 1</diffuse>
                        </material>
                    </visual>
                </link>
            </model>
        </sdf>
        """.format(model_name, BLOCK_WIDTH, BLOCK_HEIGHT)

        pose = Pose()
        pose.position.x = block[0]
        pose.position.y = block[1]
        pose.position.z = 0.5

        try:
            self.spawn_model(model_name, model_xml, '', pose, 'world')
            self.blocks[model_name] = block

        except Exception as e:
            pass

    def spawn_taxi(self, taxi):
        # Use a predefined model or a simple box to represent the taxi
        model_xml = self.get_taxi_model('yellow')  # Assuming taxi color is yellow

        pose = Pose()
        pose.position.x = taxi[0]
        pose.position.y = taxi[1]
        pose.position.z = 0.1

        try:
            model_name = 'taxi_{0}'.format(len(self.taxis) + 1)
            self.spawn_model(model_name, model_xml, '', pose, 'world')
            self.taxis[model_name] = taxi
        except Exception as e:
            pass

    def spawn_passenger(self, passenger):
        # Represent the passenger as a small cylinder
        model_xml = self.get_passenger_model('blue')  # Assuming passenger color is blue

        pose = Pose()
        pose.position.x = passenger[0]
        pose.position.y = passenger[1]
        pose.position.z = 0.1

        try:
            model_name = 'passenger_{0}'.format(len(self.passengers) + 1)
            self.spawn_model(model_name, model_xml, '', pose, 'world')
            self.passengers[model_name] = passenger
        except Exception as e:
            pass

    def handle_action(self, action):
        # Adjusted method to handle action according to your action structure
        params = action._params  # Ensure that action has _params attribute
        str_action = str(action)
        ind = str_action.find('(')
        action_name = str_action[:ind]
        print(action)

        if action_name == 'glide' or action_name.startswith('drive'):
            taxi = str(params[0])
            loc = location_to_coordinates(params[2])
            self.move_taxi(taxi, loc)
        elif action_name in ['v_to_h', 'h_to_v']:
            pass  # Handle rotations if needed
        elif action_name == 'pickup':
            taxi = str(params[0])
            pas = str(params[1])
            self.attach_passenger_to_taxi(pas, taxi)
            sleep(1)
        elif action_name == 'dropoff':
            pas = str(params[1])
            self.detach_passenger(pas)

    def attach_passenger_to_taxi(self, passenger_id, taxi_id):
        """
        Attach the passenger to the taxi by updating the mapping and moving the passenger to the taxi's pose.
        """
        try:
            # Update the mapping
            self.passenger_taxi_mapping[passenger_id] = taxi_id

            # Get the taxi's current pose
            taxi_state = self.get_model_state(taxi_id)
            if not taxi_state:
                print(f"Failed to get model state for taxi {taxi_id}")
                return

            # Set passenger's pose to match taxi's pose with an offset
            passenger_state = ModelState()
            passenger_state.model_name = passenger_id
            passenger_state.pose = taxi_state.pose
            passenger_state.pose.position.z = 1.2  # Offset passenger slightly above taxi
            self.set_model_state(passenger_state)

            print(f"Passenger {passenger_id} successfully attached to taxi {taxi_id}")

        except Exception as e:
            print(f"Error attaching passenger {passenger_id} to taxi {taxi_id}: {e}")

    def detach_passenger(self, passenger_id):
        """
        Remove the passenger from the mapping.
        """
        if passenger_id in self.passenger_taxi_mapping:
            del self.passenger_taxi_mapping[passenger_id]
            print(f"Passenger {passenger_id} successfully detached")
        else:
            print(f"Passenger {passenger_id} is not attached")

    def move_taxi(self, taxi_id, loc):
        if taxi_id not in self.taxis:
            return

        # Retrieve current position
        current_state = self.get_model_state(taxi_id)
        if not current_state:
            return

        model_state = ModelState()
        model_state.model_name = taxi_id
        model_state.pose.position.z = 0.0  # Keep it on the ground

        pose = current_state.pose

        start_x = current_state.pose.position.x
        start_y = current_state.pose.position.y

        model_state.pose.position.x = start_x
        model_state.pose.position.y = start_y

        target_x = loc[0]
        target_y = loc[1]

        quaternion = (
            pose.orientation.x,
            pose.orientation.y,
            pose.orientation.z,
            pose.orientation.w
        )

        # Convert quaternion to Euler angles (roll, pitch, yaw)
        _, _, curr_yaw = euler_from_quaternion(quaternion)

        # Calculate target yaw using atan2 for robustness
        delta_x = target_x - start_x
        delta_y = target_y - start_y
        target_yaw = math.atan2(delta_y, delta_x)

        # Rotate taxi to face target direction
        yaw_diff = target_yaw - curr_yaw
        N = 30
        yaw_step = yaw_diff / N

        # Get list of attached passengers
        attached_passengers = [pid for pid, tid in self.passenger_taxi_mapping.items() if tid == taxi_id]

        for i in range(N):
            # Convert Euler angles to quaternion
            q = quaternion_from_euler(0, 0, curr_yaw + yaw_step * (i + 1))

            # Set orientation using the quaternion
            model_state.pose.orientation.x = q[0]
            model_state.pose.orientation.y = q[1]
            model_state.pose.orientation.z = q[2]
            model_state.pose.orientation.w = q[3]
            self.set_model_state(model_state)

            # Move attached passengers
            for passenger_id in attached_passengers:
                self.move_passenger_with_taxi(passenger_id, model_state.pose)

            time.sleep(0.001)  # Adjust sleep time as needed

        # Move taxi towards the target position
        distance = math.hypot(delta_x, delta_y)
        step_size = 0.1  # Adjust as needed
        steps = max(1, int(distance / step_size))
        dx = delta_x / steps
        dy = delta_y / steps

        for i in range(steps):
            model_state.pose.position.x = start_x + dx * (i + 1)
            model_state.pose.position.y = start_y + dy * (i + 1)
            self.set_model_state(model_state)

            # Move attached passengers
            for passenger_id in attached_passengers:
                self.move_passenger_with_taxi(passenger_id, model_state.pose)

            time.sleep(0.001)  # Adjust sleep time as needed

        # Ensure final position is accurate
        model_state.pose.position.x = target_x
        model_state.pose.position.y = target_y
        self.set_model_state(model_state)

        # Move attached passengers to final position
        for passenger_id in attached_passengers:
            self.move_passenger_with_taxi(passenger_id, model_state.pose)

    def move_passenger_with_taxi(self, passenger_id, taxi_pose):
        passenger_state = ModelState()
        passenger_state.model_name = passenger_id
        passenger_state.pose = taxi_pose
        passenger_state.pose.position.z = 1.2  # Offset passenger slightly above taxi
        self.set_model_state(passenger_state)

    def get_model_state(self, model_name):
        try:
            return self.get_model_state_service(model_name, 'world')
        except Exception:
            return None

    def get_taxi_model(self, color):
        # For simplicity, represent the taxi as a colored box
        color_rgba = self.get_color_rgba(color)
        model_xml = """
        <?xml version="1.0" ?>
        <sdf version="1.6">
            <model name="taxi">
                <static>false</static>
                <link name="link">

                <gravity>false</gravity> <!-- Disable gravity -->

                    <visual name="visual">
                        <geometry>
                            <box>
                                <size>0.8 0.4 0.4</size>
                            </box>
                        </geometry>
                        <material>
                            <ambient>{0}</ambient>
                            <diffuse>{0}</diffuse>
                        </material>
                    </visual>
                </link>
            </model>
        </sdf>
        """.format(color_rgba)
        return model_xml

    def get_passenger_model(self, color):
        # Represent the passenger as a small colored cylinder
        color_rgba = self.get_color_rgba(color)
        model_xml = """
        <?xml version="1.0" ?>
        <sdf version="1.6">
            <model name="passenger">
                <static>false</static>
                <link name="link">

                    <gravity>false</gravity> <!-- Disable gravity -->

                    <visual name="visual">
                        <geometry>
                            <cylinder>
                                <radius>0.12</radius>
                                <length>0.4</length>
                            </cylinder>
                        </geometry>
                        <material>
                            <ambient>{0}</ambient>
                            <diffuse>{0}</diffuse>
                        </material>
                    </visual>
                </link>
            </model>
        </sdf>
        """.format(color_rgba)
        return model_xml

    def get_color_rgba(self, color_name):
        colors = {
            'red': '1 0 0 1',
            'green': '0 1 0 1',
            'blue': '0 0 1 1',
            'yellow': '1 1 0 1',
            'black': '0 0 0 1',
            'white': '1 1 1 1',
            'gray': '0.5 0.5 0.5 1',
            # Add more colors if needed
        }
        return colors.get(color_name.lower(), '0 0 0 1')

    def run(self):
        for action in self.actions:
            self.action_callback([action])

