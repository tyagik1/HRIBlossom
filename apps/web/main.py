from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from apps.shared.models.robot import BlossomRobot
from apps.shared.utils.sequence import get_sequence_by_name
from apps.web.sequence import SequenceRequest
from apps.shared.models.sequence import Sequence
from apps.shared.constants import get_blossom_robot

# TODO: Complete blockly app to create custom gestures.

app = FastAPI()

robot: BlossomRobot = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_robot():
    """Get or initialize the robot instance"""
    global robot
    if robot is None:
        try:
            robot = get_blossom_robot()
            print("Robot initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize robot: {e}")
            print("Running in simulation mode")
            robot = None
    return robot


@app.get("/")
async def handle_root():
    return {
        "message": "Blossom Robot Control API",
        "version": "1.0",
        "robot_connected": robot is not None
    }


@app.post("/reset")
async def handle_reset():
    """Reset the robot to its default position"""
    try:
        sequence = get_sequence_by_name("reset")
        sequence.start()
        sequence.wait_to_stop()
        return {
            "message": "Robot reset successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset robot: {str(e)}")

@app.get("/sequences")
async def handle_get_sequences():
    pass

@app.get("/sequences/{sequence_id}")
async def handle_get_sequence(sequence_id: str):
    pass

@app.get("/sequences/names")
async def handle_get_sequence_by_name():
    pass

@app.post("/sequences")
async def handle_create_sequence(sequence: SequenceRequest):
    # TODO: Implement sequence storage
    pass

@app.get("/sequences/{sequence_id}/play")
async def handle_play_sequence(sequence_id: str):
    pass

@app.get("/sequences/{sequence_id}/stop")
async def handle_stop_sequence(sequence_id: str):
    pass

@app.get("/sequences/{sequence_id}/pause")
async def handle_pause_sequence(sequence_id: str):
    pass

@app.post("/sequences/play")
async def handle_play_custom_sequence(sequence_data: SequenceRequest):
    """
    Play a custom animation sequence.
    
    The sequence is validated against the Sequence model and then executed on the robot.
    """
    try:
        robot_instance = get_robot()
        
        print(f"\n{'='*60}")
        print(f"Received sequence: {sequence_data.animation}")
        print(f"Number of frames: {len(sequence_data.frame_list)}")
        print(f"{'='*60}\n")
        
        if robot_instance is None:
            print(f"Animation: {sequence_data.animation}")
            
            for i, frame in enumerate(sequence_data.frame_list):
                print(f"\nFrame {i+1} at {frame.millis}ms:")
                for pos in frame.positions:
                    print(f"  {pos.dof}: {pos.pos}")
            
            return {
                "message": f"Sequence '{sequence_data.animation}' completed (simulation)",
                "animation": sequence_data.animation,
                "frame_count": len(sequence_data.frame_list),
                "simulation": True
            }
        
        sequence = Sequence(
            robot=robot_instance,
            animation=sequence_data.animation,
            frames=sequence_data.frame_list
        )
        
        print(f"Starting playback of sequence: {sequence_data.animation}")
        sequence.start()
        sequence.wait_to_stop()
        
        return {
            "message": f"Sequence '{sequence_data.animation}' completed successfully",
            "animation": sequence_data.animation,
            "frame_count": len(sequence_data.frame_list),
            "duration_ms": sequence_data.frame_list[-1].millis if sequence_data.frame_list else 0,
            "simulation": False
        }
        
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Validation error",
                "details": e.errors()
            }
        )
    except Exception as e:
        print(f"Error playing sequence: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to play sequence: {str(e)}"
        )