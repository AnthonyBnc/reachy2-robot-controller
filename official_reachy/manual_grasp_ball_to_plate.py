#import the package
from reachy2_sdk import ReachySDK 

#connect to the robot
reachy = ReachySDK('localhost') # replace 'localhost' with the actual IP address of your Reachy
print("Reachy is connected :", reachy.is_connected())

mujoco_mode = False # set to True if you want to use the MuJoCo simulator

from pollen_vision.camera_wrappers.pollen_sdk_camera.pollen_sdk_camera_wrapper import PollenSDKCameraWrapper

# instanciation of the camera wrapper
r_cam = PollenSDKCameraWrapper(reachy)

# get the image as a np.array, and the timestamp of the image
data, _, timestamp = r_cam.get_data()

# displays the image from the RGB camera (depth camera is available by changing 'left' to 'depth')
from PIL import Image
img = data['left']
Image.fromarray(img) 

from reachy2_sdk.utils.utils import invert_affine_transformation_matrix

T_cam_reachy = reachy.cameras.depth.get_extrinsics()
T_reachy_cam = invert_affine_transformation_matrix(T_cam_reachy)

from pollen_vision.vision_models.object_detection import YoloWorldWrapper
from pollen_vision.utils import get_bboxes
from pollen_vision.utils import Annotator

# those first labels won't be good enough
labels = ["orange", "apple", "plate", "bowl"]

yolo = YoloWorldWrapper() # allows to use the YOLO model for object detection
yolo._model.model = yolo._model.model.to("cpu")
annotator = Annotator() # allows to get annotated image with the detected objects
yolo_predictions = yolo.infer(im=img[:,:,::-1], candidate_labels=labels, detection_threshold=0.15) 
bboxes = get_bboxes(yolo_predictions) # returns the bounding boxes of the detected objects
img_annotated = annotator.annotate(im=img, detection_predictions=yolo_predictions) 
Image.fromarray(img_annotated)