import { useState } from "react";
import { DropZone } from "./components/DropZone";

function App() {
  const [file, setFile] = useState<File | null>(null);

  return (
    <div style={{ maxWidth: 800, margin: "40px auto", padding: "0 20px" }}>
      <h1>Image to DXF Converter</h1>
      <DropZone onFileSelect={setFile} />
      {file && <p>Selected: {file.name}</p>}
    </div>
  );
}

export default App;
