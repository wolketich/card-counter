// Belot Score Calculator for belot.md
(function() {
    console.log("Belot Automation Script started...");
    
    // Configuration
    const USER = "wolketich";
    const DATE = "2025-04-23 09:47:06";
    
    // Combination point values - exactly as provided
    const COMBINATIONS = [
        { name: "Tărț", points: 20 },
        { name: "Bella", points: 20 },
        { name: "Jumate de Sută", points: 50 },
        { name: "O Sută", points: 100 },
        { name: "Patru cărți de 10", points: 100 },
        { name: "Patru cărți de J", points: 200 },
        { name: "Patru cărți de A", points: 100 },
        { name: "Patru cărți de Q", points: 100 },
        { name: "Patru cărți de K", points: 100 },
        { name: "Patru cărți de 9", points: 150 }
    ];
    
    // Romanian suit names mapping - corrected
    const SUIT_SYMBOLS = {
        'Verde': '♠',
        'Verde': '♠',
        'Roșu': '♥',
        'Rosu': '♥',
        'Dobă': '♦',
        'Cruce': '♣'
    };
    
    // State variables
    let clipboardText = null;
    let resultShown = false;
    
    // Listen for the start button click
    document.getElementById('js__count-cards-start').addEventListener('click', function() {
        console.log("Start button clicked, copying image...");
        resultShown = false;
        setTimeout(copyCardImage, 1000); // Wait a moment for the page to update
    });
    
    // Function to copy the card image to clipboard
    function copyCardImage() {
        const imgElement = document.querySelector('.js__count-cards-swiper-img');
        if (!imgElement) {
            console.error("Could not find card image element!");
            return;
        }
        
        // Create a canvas to draw the image
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // Create a new image to load the src URL
        const image = new Image();
        image.crossOrigin = "Anonymous";
        
        image.onload = function() {
            // Set canvas size to match image
            canvas.width = image.width;
            canvas.height = image.height;
            
            // Draw image to canvas
            ctx.drawImage(image, 0, 0);
            
            // Convert to blob and copy to clipboard
            canvas.toBlob(function(blob) {
                const item = new ClipboardItem({ "image/png": blob });
                navigator.clipboard.write([item]).then(function() {
                    console.log("Image copied to clipboard successfully");
                    // Start checking for clipboard update
                    startClipboardCheck();
                }, function(err) {
                    console.error("Could not copy image: ", err);
                });
            });
        };
        
        // Handle errors
        image.onerror = function() {
            console.error("Failed to load image from URL:", imgElement.src);
            
            // Try to fetch as blob instead (CORS workaround)
            fetch(imgElement.src)
                .then(response => response.blob())
                .then(blob => {
                    const url = URL.createObjectURL(blob);
                    const img = new Image();
                    img.onload = function() {
                        canvas.width = img.width;
                        canvas.height = img.height;
                        ctx.drawImage(img, 0, 0);
                        canvas.toBlob(function(blob) {
                            const item = new ClipboardItem({ "image/png": blob });
                            navigator.clipboard.write([item]).then(function() {
                                console.log("Image copied to clipboard via blob workaround");
                                startClipboardCheck();
                            });
                        });
                    };
                    img.src = url;
                })
                .catch(err => console.error("Failed to fetch image:", err));
        };
        
        // Start loading image
        image.src = imgElement.src;
    }
    
    // Check for clipboard update with text results
    function startClipboardCheck() {
        console.log("Starting clipboard monitoring...");
        
        const checkInterval = setInterval(function() {
            navigator.clipboard.readText().then(function(text) {
                if (text && text.includes("=== BELOT CARD CALCULATOR ===")) {
                    clearInterval(checkInterval);
                    clipboardText = text;
                    console.log("Card calculation results detected in clipboard");
                    calculateFinalScore();
                }
            }).catch(err => {
                console.error("Error reading clipboard:", err);
            });
        }, 1000);
        
        // Timeout after 20 seconds
        setTimeout(function() {
            clearInterval(checkInterval);
            console.log("Clipboard monitoring timed out");
        }, 20000);
    }
    
    // Parse clipboard text to extract points by suit
    function parsePointsFromClipboard(text) {
        const pointsBySuit = {};
        const lines = text.split('\n');
        let inPointsSection = false;
        
        for (const line of lines) {
            if (line.includes("POINTS BY TRUMP SUIT:")) {
                inPointsSection = true;
                continue;
            }
            
            if (inPointsSection && line.trim() === "") {
                break; // End of points section
            }
            
            if (inPointsSection) {
                // Example: "Doba (♠): 77 points"
                const match = line.match(/(.*) \(([♠♥♦♣])\): (\d+) points/);
                if (match) {
                    const suitName = match[1];
                    const suit = match[2];
                    const points = parseInt(match[3]);
                    pointsBySuit[suit] = points;
                }
            }
        }
        
        return pointsBySuit;
    }
    
    // Calculate points from combinations text using the list
    function calculateCombinationPoints(combinationsText) {
        if (!combinationsText || combinationsText.trim() === "") {
            return { points: 0, details: "Fără combinații" };
        }
        
        // Special cases for game cancellation
        if (combinationsText.includes("Patru") && combinationsText.includes("șapte")) {
            return { points: 0, details: "Game canceled - Patru cărți de șapte" };
        }
        if (combinationsText.includes("Patru") && combinationsText.includes("opt")) {
            return { points: 0, details: "All combinations canceled - Patru cărți de opt" };
        }
        
        // Find all mentioned combinations
        let totalPoints = 0;
        let detectedCombinations = [];
        
        // Simple detection based on key phrases
        for (const combo of COMBINATIONS) {
            // Create simplified versions for matching
            const simpleName = combo.name.toLowerCase()
                .replace(/ă/g, "a")
                .replace(/ț/g, "t")
                .replace(/ș/g, "s");
                
            const simpleText = combinationsText.toLowerCase()
                .replace(/ă/g, "a")
                .replace(/ț/g, "t")
                .replace(/ș/g, "s");
            
            // Simple keyword matching
            if (simpleText.includes(simpleName) || 
                // Special case for Bella/Bela
                (combo.name === "Bella" && simpleText.includes("bela")) ||
                // Special case for Tărț/Terț/Tert
                (combo.name === "Tărț" && (simpleText.includes("tert") || simpleText.includes("tart"))) ||
                // Special case for Jumate de Sută/50
                (combo.name === "Jumate de Sută" && (simpleText.includes("jumate") || simpleText.includes("50"))) ||
                // Special case for O Sută/100
                (combo.name === "O Sută" && (simpleText.includes("suta") || simpleText.includes("100")))) {
                
                totalPoints += combo.points;
                detectedCombinations.push(`${combo.name}: +${combo.points}`);
            }
        }
        
        return { 
            points: totalPoints, 
            details: detectedCombinations.join(", ") || "Fără combinații"
        };
    }
    
    // Calculate final score
    function calculateFinalScore() {
        // Parse points from clipboard
        const pointsBySuit = parsePointsFromClipboard(clipboardText);
        
        // Get trump suit from the page
        const cozElement = document.querySelector('.count-cards__wrapper__game__main__cards__coz .info');
        let trumpSuit = null;
        let trumpName = null;
        
        if (cozElement) {
            const match = cozElement.innerText.match(/Cozul: (.*)/);
            if (match && match[1]) {
                trumpName = match[1].trim();
                trumpSuit = SUIT_SYMBOLS[trumpName];
                console.log(`Trump suit identified as ${trumpName} (${trumpSuit})`);
            }
        }
        
        if (!trumpSuit) {
            console.error("Could not determine trump suit!");
            return;
        }
        
        // Get trump suit points
        const trumpPoints = pointsBySuit[trumpSuit] || 0;
        console.log(`Base points from trump suit (${trumpSuit}): ${trumpPoints}`);
        
        // Get combinations from the page
        const combElement = document.querySelector('.count-cards__wrapper__game__main__cards__combinations .info');
        let combinationsText = "";
        
        if (combElement) {
            combinationsText = combElement.innerText.trim();
            console.log(`Combinations identified: ${combinationsText}`);
        }
        
        // Calculate combination points
        const combinationResult = calculateCombinationPoints(combinationsText);
        
        // Check for game canceled
        if (combinationResult.details.includes("Game canceled")) {
            displayResult("ANULAT", "Jocul este anulat (Patru de șapte)");
            return;
        }
        
        // Add combination points to trump points
        const finalScore = trumpPoints + combinationResult.points;
        console.log(`Final score: ${finalScore} (Trump: ${trumpPoints}, Combinations: ${combinationResult.points})`);
        
        // Display the final result
        const details = `Coz: ${trumpName} (${trumpPoints}) + ${combinationResult.details} = ${finalScore}`;
        displayResult(finalScore, details);
    }
    
    // Display the final result on the page
    function displayResult(score, details) {
        if (resultShown) return;
        resultShown = true;
        
        // Create result element
        const resultElement = document.createElement('div');
        resultElement.className = 'belot-result';
        resultElement.style.cssText = 'background: #fff; border: 2px solid #4CAF50; padding: 15px; margin: 15px auto; max-width: 400px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center;';
        
        // Create content
        resultElement.innerHTML = `
            <h3 style="margin: 0 0 10px; color: #333; font-size: 20px;">Rezultat Final</h3>
            <div style="font-size: 28px; font-weight: bold; color: #4CAF50; margin: 10px 0;">${score} puncte</div>
            <div style="font-size: 14px; color: #666; margin-top: 10px;">${details}</div>
            <div style="font-size: 12px; color: #999; margin-top: 15px;">Calculat de ${USER} - ${DATE}</div>
        `;
        
        // Insert before the input form
        const formElement = document.querySelector('.form-full');
        if (formElement && formElement.parentNode) {
            formElement.parentNode.insertBefore(resultElement, formElement);
            
            // Also update the input field with the score value
            const inputElement = document.getElementById('js__count-cards-input');
            if (inputElement && typeof score === 'number') {
                inputElement.value = score;
                
                // Trigger a focus and blur event to make sure it's recognized
                inputElement.focus();
                inputElement.blur();
                
                // Enable the submit button
                const submitButton = document.getElementById('js__count-cards-result-submit');
                if (submitButton) {
                    submitButton.classList.remove('hidden');
                }
            }
        }
    }
    
    console.log("Belot Automation Script ready!");
})();