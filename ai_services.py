import os
import json
import httpx
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


async def transcribe_audio(file_path: str) -> str:
    """Transcribe audio file using OpenAI Whisper API"""
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            return "Error: OPENAI_API_KEY not set"
        
        async with httpx.AsyncClient() as client:
            with open(file_path, 'rb') as audio_file:
                files = {
                    'file': (Path(file_path).name, audio_file, 'audio/mpeg'),
                    'model': (None, 'whisper-1')
                }
                headers = {'Authorization': f'Bearer {openai_api_key}'}
                
                response = await client.post(
                    'https://api.openai.com/v1/audio/transcriptions',
                    files=files,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('text', '')
                else:
                    return f"Transcription failed: {response.status_code}"
    
    except Exception as e:
        return f"Transcription error: {str(e)}"


async def extract_entities_from_text(text: str) -> dict:
    """Extract maintenance-related entities from text using OpenAI"""
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            return {"error": "OPENAI_API_KEY not set"}
        
        prompt = f"""
        Extract maintenance-related information from the following text and return a JSON object with these fields:
        - equipment_ids: array of equipment identifiers
        - part_numbers: array of part numbers
        - defect_codes: array of defect/issue codes
        - priority: one of "low", "medium", "high", "critical"
        - description: brief summary of the issue
        
        Text: {text}
        
        Return only valid JSON:
        """
        
        async with httpx.AsyncClient() as client:
            headers = {
                'Authorization': f'Bearer {openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': 'You are a maintenance expert. Extract structured data from maintenance reports.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3
            }
            
            response = await client.post(
                'https://api.openai.com/v1/chat/completions',
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return {"error": "Invalid JSON response", "raw_content": content}
            else:
                return {"error": f"API request failed: {response.status_code}"}
    
    except Exception as e:
        return {"error": f"Entity extraction error: {str(e)}"}


async def generate_maintenance_report(items_data: list) -> dict:
    """Generate a structured maintenance report from processed items"""
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            return {"error": "OPENAI_API_KEY not set"}
        
        # Combine all transcriptions and extracted data
        combined_text = ""
        all_entities = {
            "equipment_ids": [],
            "part_numbers": [],
            "defect_codes": [],
            "descriptions": []
        }
        
        for item in items_data:
            if item.get('transcription'):
                combined_text += f"\n{item['transcription']}"
            if item.get('extracted_data'):
                try:
                    entities = json.loads(item['extracted_data'])
                    all_entities["equipment_ids"].extend(entities.get("equipment_ids", []))
                    all_entities["part_numbers"].extend(entities.get("part_numbers", []))
                    all_entities["defect_codes"].extend(entities.get("defect_codes", []))
                    all_entities["descriptions"].append(entities.get("description", ""))
                except json.JSONDecodeError:
                    pass
        
        prompt = f"""
        Create a comprehensive maintenance report based on the following information:
        
        Combined Text: {combined_text}
        
        Extracted Entities:
        - Equipment IDs: {list(set(all_entities["equipment_ids"]))}
        - Part Numbers: {list(set(all_entities["part_numbers"]))}
        - Defect Codes: {list(set(all_entities["defect_codes"]))}
        
        Generate a JSON report with these fields:
        - title: descriptive title
        - description: detailed problem description
        - equipment_id: primary equipment identifier
        - part_numbers: array of relevant part numbers
        - defect_codes: array of defect codes
        - corrective_action: recommended actions
        - parts_used: array of parts that should be used
        - next_service_date: suggested next service date (ISO format)
        - priority: "low", "medium", "high", or "critical"
        
        Return only valid JSON:
        """
        
        async with httpx.AsyncClient() as client:
            headers = {
                'Authorization': f'Bearer {openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': 'You are a maintenance expert creating structured reports from field data.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3
            }
            
            response = await client.post(
                'https://api.openai.com/v1/chat/completions',
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return {"error": "Invalid JSON response", "raw_content": content}
            else:
                return {"error": f"API request failed: {response.status_code}"}
    
    except Exception as e:
        return {"error": f"Report generation error: {str(e)}"}


async def detect_entities_in_image(image_path: str, entity_type: str) -> dict:
    """Detect entities in image using Moondream API and create preview with bounding boxes"""
    try:
        # Import moondream here to avoid dependency issues if not installed
        import moondream as md
        
        # Get API key from environment
        moondream_api_key = os.getenv("MOONDREAM_API_KEY")
        if not moondream_api_key:
            return {"error": "MOONDREAM_API_KEY not set"}
        
        # Initialize model with API key
        model = md.vl(api_key=moondream_api_key)
        
        # Load the original image
        original_image = Image.open(image_path)
        
        # Detect entities
        result = model.detect(original_image, entity_type)
        detections = result["objects"]
        request_id = result.get("request_id", "unknown")
        
        if not detections:
            return {
                "success": True,
                "detections": [],
                "count": 0,
                "request_id": request_id,
                "message": f"No {entity_type} entities found in the image"
            }
        
        # Create a copy for preview (don't modify original)
        preview_image = original_image.copy()
        draw = ImageDraw.Draw(preview_image)
        
        # Try to load a font, fall back to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except IOError:
            try:
                # Try common system fonts
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 12)  # macOS
            except IOError:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)  # Linux
                except IOError:
                    font = ImageFont.load_default()
        
        # Process each detection
        detection_data = []
        for i, obj in enumerate(detections):
            # Convert normalized coordinates to pixel values
            x_min = int(obj["x_min"] * original_image.width)
            y_min = int(obj["y_min"] * original_image.height)
            x_max = int(obj["x_max"] * original_image.width)
            y_max = int(obj["y_max"] * original_image.height)
            
            # Draw the bounding box rectangle
            draw.rectangle([x_min, y_min, x_max, y_max], outline="red", width=2)
            
            # Draw the label text
            label = f"{entity_type.title()} {i+1}"
            draw.text((x_min, y_min - 15), label, fill="white", font=font)
            
            # Store detection data
            detection_data.append({
                "index": i + 1,
                "x_min": obj["x_min"],
                "y_min": obj["y_min"], 
                "x_max": obj["x_max"],
                "y_max": obj["y_max"],
                "pixel_coords": {
                    "x_min": x_min,
                    "y_min": y_min,
                    "x_max": x_max,
                    "y_max": y_max
                }
            })
        
        # Create preview image path
        image_path_obj = Path(image_path)
        preview_path = image_path_obj.parent / f"{image_path_obj.stem}_preview{image_path_obj.suffix}"
        
        # Save the preview image (don't modify original)
        preview_image.save(preview_path)
        
        return {
            "success": True,
            "detections": detection_data,
            "count": len(detections),
            "request_id": request_id,
            "preview_path": str(preview_path),
            "original_path": image_path,
            "entity_type": entity_type,
            "message": f"Found {len(detections)} {entity_type} entities"
        }
        
    except ImportError:
        return {"error": "Moondream library not installed. Please install with: pip install moondream"}
    except Exception as e:
        return {"error": f"Entity detection error: {str(e)}"}