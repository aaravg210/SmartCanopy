""" 
Test DeepForest tree detection on downloaded imagery
"""

from deepforest import main
import matplotlib.pyplot as plt
from PIL import Image
import os

class DeepForestDetector:
    """Detects trees in satellite imagery using DeepForest"""
    
    def __init__(self):
        """Initialize and load DeepForest model"""
        print("Loading DeepForest model...")
        self.model = main.deepforest()
        self.model.use_release()  # Load pre-trained weights
        print("✓ Model loaded!\n")
    
    def predict_trees(self, image_path: str, confidence_threshold: float = 0.3):
        """
        Detect trees in an image
        
        Args:
            image_path: Path to RGB image file
            
        Returns:
            DataFrame with bounding boxes
        """
        # Check if file exists
        if not os.path.exists(image_path):
            print(f"✗ File not found: {image_path}")
            return None
        
        print(f"Detecting trees in: {image_path}\n")
        
        # Predict trees
        predictions = self.model.predict_image(path=image_path, return_plot=False)
        # Filter by confidence threshold
        if len(predictions) > 0:
            predictions = predictions[predictions['score'] >= confidence_threshold]
            print(f"After filtering (threshold={confidence_threshold}): {len(predictions)} trees")

        print(f"✓ Detected {len(predictions)} trees!\n")
        
        # Show first few predictions
        if len(predictions) > 0:
            print("First 5 detections:")
            print(predictions.head())
            print(f"\nConfidence scores range: {predictions['score'].min():.2f} to {predictions['score'].max():.2f}")
        else:
            print("No trees detected")
            
        return predictions
    
    def visualize_predictions(self, image_path: str, predictions):
        """
        Create visualization with bounding boxes
        
        Args:
            image_path: Path to original image
            predictions: DataFrame from predict_trees()
        """
        if predictions is None or len(predictions) == 0:
            print("No predictions to visualize")
            return
        
        print("\nGenerating visualization...")
        
        # Load original image
        image = Image.open(image_path)
        
        # Create figure with 2 subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Left: Original image
        ax1.imshow(image)
        ax1.set_title('Original Image')
        ax1.axis('off')
        
        # Right: Image with detections
        ax2.imshow(image)
        for _, row in predictions.iterrows():
            xmin, ymin, xmax, ymax = row['xmin'], row['ymin'], row['xmax'], row['ymax']
            # Draw red bounding box
            ax2.plot([xmin, xmax, xmax, xmin, xmin], 
                     [ymin, ymin, ymax, ymax, ymin], 
                     'r-', linewidth=2)
        ax2.set_title(f'Detected Trees ({len(predictions)} found)')
        ax2.axis('off')
        
        plt.tight_layout()
        
        # Save visualization
        output_path = image_path.replace('.png', '_detections.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"✓ Visualization saved to: {output_path}")
        
        # Show the plot
        plt.show()
        
        return output_path


if __name__ == "__main__":
    # Initialize detector
    detector = DeepForestDetector()
    
    # Your image path
    image_path = "analysis_data/5826_Brasilia_Way_San_Jose_CA_rgb.png"
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"✗ File not found: {image_path}")
        print("\nAvailable files in test_data/:")
        if os.path.exists("test_data"):
            for f in os.listdir("test_data"):
                print(f"  - {f}")
        else:
            print("  test_data folder doesn't exist!")
        exit()
    
    # Detect trees
    predictions = detector.predict_trees(image_path)
    
    # Visualize results
    if predictions is not None and len(predictions) > 0:
        detector.visualize_predictions(image_path, predictions)
        print("\nSUCCESS! Tree detection is working!")
    else:
        print("\nNo trees detected")
