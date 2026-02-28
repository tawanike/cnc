import { useState } from "react";
import { DropZone } from "./components/DropZone";
import { ScaleInput } from "./components/ScaleInput";

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [targetWidthMm, setTargetWidthMm] = useState("");
  const [targetHeightMm, setTargetHeightMm] = useState("");

  return (
    <div style={{ maxWidth: 800, margin: "40px auto", padding: "0 20px" }}>
      <h1>Image to DXF Converter</h1>
      <DropZone onFileSelect={setFile} />
      {file && (
        <>
          <ScaleInput
            targetWidthMm={targetWidthMm}
            targetHeightMm={targetHeightMm}
            onWidthChange={setTargetWidthMm}
            onHeightChange={setTargetHeightMm}
          />
        </>
      )}
    </div>
  );
}

export default App;
