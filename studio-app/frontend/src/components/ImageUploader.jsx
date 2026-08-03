import { useRef, useState } from "react";
import { IconClose } from "./Icons.jsx";

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
  });
}

export default function ImageUploader({ maxImages, images, onChange }) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef(null);

  const addFiles = async (fileList) => {
    const files = Array.from(fileList).slice(0, maxImages - images.length);
    const encoded = await Promise.all(files.map(fileToBase64));
    onChange([...images, ...encoded].slice(0, maxImages));
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    addFiles(event.dataTransfer.files);
  };

  const removeImage = (index) => {
    onChange(images.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-3">
      <div
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`cursor-pointer rounded-lg border-2 border-dashed p-6 text-center text-sm transition-colors ${
          isDragging
            ? "border-accent bg-accent/10 text-accent"
            : "border-neutral-300 text-neutral-500 hover:border-neutral-400"
        }`}
      >
        {images.length >= maxImages
          ? `Maximum of ${maxImages} image${maxImages > 1 ? "s" : ""} reached`
          : "Drag & drop an image, or click to upload / take a photo"}
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png"
          capture="environment"
          multiple={maxImages > 1}
          className="hidden"
          onChange={(event) => {
            if (event.target.files?.length) addFiles(event.target.files);
            event.target.value = "";
          }}
        />
      </div>

      {images.length > 0 && (
        <div className="flex flex-wrap gap-3">
          {images.map((src, index) => (
            <div key={index} className="relative">
              <img
                src={src}
                alt={`Upload ${index + 1}`}
                className="h-24 w-24 rounded-md object-cover border border-neutral-200"
              />
              <button
                type="button"
                onClick={() => removeImage(index)}
                className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-white border border-neutral-300 text-neutral-500 hover:border-accent hover:text-accent"
              >
                <IconClose className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
