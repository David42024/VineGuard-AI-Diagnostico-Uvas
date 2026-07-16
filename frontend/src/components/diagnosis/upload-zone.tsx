"use client";

import { useState, useRef, DragEvent } from "react";
import { Upload, X, Image as ImageIcon, FileWarning } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  selectedFile?: File | null;
  preview?: string;
  onRemove: () => void;
}

export function UploadZone({
  onFileSelect,
  selectedFile,
  preview,
  onRemove,
}: UploadZoneProps) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): boolean => {
    const validTypes = ["image/jpeg", "image/png", "image/webp", "image/jpg"];
    if (!validTypes.includes(file.type)) {
      setError("Formato no soportado. Use JPG, PNG o WebP.");
      return false;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("La imagen no debe superar los 10MB.");
      return false;
    }
    setError("");
    return true;
  };

  const handleDrag = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragging(true);
    } else if (e.type === "dragleave") {
      setDragging(false);
    }
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file && validateFile(file)) {
      onFileSelect(file);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && validateFile(file)) {
      onFileSelect(file);
    }
  };

  return (
    <div className="space-y-4">
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "relative flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors",
          dragging
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/50",
          selectedFile && "border-solid border-primary"
        )}
      >
        {preview ? (
          <div className="relative w-full max-w-xs mx-auto">
            <img
              src={preview}
              alt="Preview"
              className="max-h-64 rounded-lg object-contain mx-auto"
            />
            <Button
              variant="destructive"
              size="icon"
              className="absolute -right-2 -top-2 h-6 w-6"
              onClick={(e) => {
                e.stopPropagation();
                onRemove();
              }}
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
        ) : (
          <>
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
              <Upload className="h-6 w-6 text-primary" />
            </div>
            <p className="mb-1 text-sm font-medium">
              Arrastra una imagen aquí o haz clic para seleccionar
            </p>
            <p className="text-xs text-muted-foreground">
              JPG, PNG o WebP. Máximo 10MB.
            </p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={handleChange}
        />
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
          <FileWarning className="h-4 w-4" />
          {error}
        </div>
      )}

      {selectedFile && !error && (
        <p className="text-sm text-muted-foreground text-center">
          {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
        </p>
      )}
    </div>
  );
}
