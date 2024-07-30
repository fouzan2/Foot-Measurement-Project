import os
import base64
import json
import math
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import FootImageForm
from inference_sdk import InferenceHTTPClient

# Initialize the InferenceHTTPClient
CLIENT = InferenceHTTPClient(
    api_url="https://outline.roboflow.com",
    api_key="lP0Yx58hBgkr8BlLnoot"
)

# Conversion factor from pixels to centimeters (adjust based on your setup)
PIXEL_TO_CM_CONVERSION_FACTOR = 0.0264  # Example factor, adjust as needed

def process_image_with_client(image_path, model_id):
    result = CLIENT.infer(image_path, model_id=model_id)
    return result

def measure_dimensions_from_result(result):
    boxes = result['predictions']
    if len(boxes) == 0:
        raise Exception("No foot detected in the image")
    box = boxes[0]
    x_min, y_min, width, height = box['x'], box['y'], box['width'], box['height']
    x_max = x_min + width
    y_max = y_min + height
    length_pixels = math.sqrt((x_max - x_min) ** 2 + (y_max - y_min) ** 2)
    
    # Convert pixels to centimeters
    length_cm = length_pixels * PIXEL_TO_CM_CONVERSION_FACTOR
    height_cm = height * PIXEL_TO_CM_CONVERSION_FACTOR

    new_length = length_cm + 4
    new_height = height_cm + 4
    
    return new_length, new_height

@csrf_exempt
def measure_foot(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_data = data['image']
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]
            image_data = base64.b64decode(imgstr)
            
            # Save the image to a file (optional)
            media_root = settings.MEDIA_ROOT
            if not os.path.exists(media_root):
                os.makedirs(media_root)
            image_path = os.path.join(media_root, f"uploaded_image.{ext}")
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            # Use the InferenceHTTPClient to process the image
            model_id = "foot-detection-updated/1"
            result = process_image_with_client(image_path, model_id)
            new_length, new_height = measure_dimensions_from_result(result)
            
            return JsonResponse({
                'length': new_length,
                'height': new_height
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def upload_page(request):
    if request.method == 'POST':
        form = FootImageForm(request.POST, request.FILES)
        if form.is_valid():
            image_file = form.cleaned_data['image']
            media_root = settings.MEDIA_ROOT
            if not os.path.exists(media_root):
                os.makedirs(media_root)
            image_path = os.path.join(media_root, image_file.name)
            with open(image_path, 'wb+') as destination:
                for chunk in image_file.chunks():
                    destination.write(chunk)
            
            # Use the InferenceHTTPClient to process the image
            model_id = "foot-detection-updated/1"
            result = process_image_with_client(image_path, model_id)
            new_length, new_height = measure_dimensions_from_result(result)
            
            return render(request, 'result.html', {'length': new_length,'height': new_height})
    else:
        form = FootImageForm()
    return render(request, 'upload.html', {'form': form})

def results(request):
    length = request.GET.get('length')
    height = request.GET.get('height')
    return render(request, 'result.html', {'length': length, 'height': height})