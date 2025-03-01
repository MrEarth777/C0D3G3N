import React, { useState } from "react";
import CodeConverter from "./CodeConverter";
import History from "./History";

function App() {
    const [view, setView] = useState("convert");

    return (
        <div>
            <h1>C0d3g3n - Legacy Code Converter</h1>
            <nav>
                <button onClick={() => setView("convert")}>Converteren</button>
                <button onClick={() => setView("history")}>Geschiedenis</button>
            </nav>

            {view === "convert" ? <CodeConverter /> : <History />}
        </div>
    );
}

export default App;
