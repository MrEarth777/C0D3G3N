import React, { useState } from "react";

function CodeConverter() {
    const [legacyCode, setLegacyCode] = useState("");
    const [modernCode, setModernCode] = useState("");

    const convertCode = async () => {
        const response = await fetch("http://127.0.0.1:8000/convert/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ legacy_code: legacyCode, source_language: "COBOL", target_language: "Python" }),
        });
        const data = await response.json();
        setModernCode(data);
    };

    return (
        <div>
            <h2>Legacy Code Converter</h2>
            <textarea value={legacyCode} onChange={(e) => setLegacyCode(e.target.value)} />
            <button onClick={convertCode}>Convert</button>
            <pre>{modernCode}</pre>
        </div>
    );
}

export default CodeConverter;
