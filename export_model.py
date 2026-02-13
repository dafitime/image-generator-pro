import torch
import torchvision.models as models

def export_model():
    print("⬇️ Downloading pre-trained ResNet50 model...")
    # Load a standard pre-trained model
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
    model.eval()

    # Create a dummy input (needed so ONNX knows the image size)
    # Batch size 1, 3 channels (RGB), 224x224 resolution
    dummy_input = torch.randn(1, 3, 224, 224)

    print("📦 Exporting to ONNX format...")
    torch.onnx.export(
        model,
        dummy_input,
        "image_tagger.onnx",  # Output file
        export_params=True,
        opset_version=11,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
    )
    
    # Download the labels (human readable names for the tags)
    import urllib.request
    print("📝 Downloading ImageNet labels...")
    url = "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt"
    urllib.request.urlretrieve(url, "imagenet_classes.txt")

    print("✅ Done! You now have 'image_tagger.onnx' and 'imagenet_classes.txt'.")

if __name__ == "__main__":
    export_model()