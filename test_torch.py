import torch

def check_cuda():
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print("\n=== CUDA Details ===")
        print(f"CUDA version: {torch.version.cuda}")
        print(f"Number of GPUs: {torch.cuda.device_count()}")
        print(f"Current device: {torch.cuda.current_device()}")
        print(f"Device name: {torch.cuda.get_device_name(0)}")
        print(f"Device capability: {torch.cuda.get_device_capability(0)}")
        
        # Memory info
        print("\n=== Memory Info ===")
        print(f"Allocated: {torch.cuda.memory_allocated(0)/1024**2:.2f} MB")
        print(f"Cached: {torch.cuda.memory_reserved(0)/1024**2:.2f} MB")
        
        # Performance check
        print("\n=== Performance Test ===")
        a = torch.randn(1000, 1000).cuda()
        b = torch.randn(1000, 1000).cuda()
        torch.cuda.synchronize()  # Wait for CUDA ops to finish
        print("Matrix multiplication test passed!")
    else:
        print("\nCUDA is not properly configured")

if __name__ == "__main__":
    check_cuda()