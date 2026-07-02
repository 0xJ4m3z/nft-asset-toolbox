if __name__ == "__main__":
    try:
        from nft_asset_toolbox.app import main
    except ImportError as exc:
        print("Unable to start NFT Asset Toolbox desktop UI.")
        print("Install Python dependencies with: python -m pip install -r requirements.txt")
        print("On Linux, PySide6 may also require the system Qt/OpenGL runtime, such as libGL.so.1.")
        print(f"Import error: {exc}")
        raise SystemExit(1)

    raise SystemExit(main())
