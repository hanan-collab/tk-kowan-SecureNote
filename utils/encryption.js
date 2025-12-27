// =================
// UTILITY FUNCTIONS
// =================

function buffToHex(buffer) {
    return Array.from(new Uint8Array(buffer))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
}

function hexToBuff(hexString) {
    return new Uint8Array(hexString.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
}

// =================
// CORE CRYPTO LOGIC
// =================

async function deriveKeys(password, saltBuffer) {
    const enc = new TextEncoder();

    const keyMaterial = await window.crypto.subtle.importKey(
        "raw",
        enc.encode(password),
        { name: "PBKDF2" },
        false,
        ["deriveBits"]
    );

    const masterBits = await window.crypto.subtle.deriveBits(
        {
            name: "PBKDF2",
            salt: saltBuffer,
            iterations: 100000,
            hash: "SHA-256"
        },
        keyMaterial,
        256
    );

    const masterKey = await window.crypto.subtle.importKey(
        "raw",
        masterBits,
        { name: "HKDF" },
        false,
        ["deriveKey"]
    );

    const keyEncrypt = await window.crypto.subtle.deriveKey(
        {
            name: "HKDF",
            salt: new Uint8Array(),
            info: enc.encode("key_encrypt"),
            hash: "SHA-256"
        },
        masterKey,
        { name: "AES-GCM", length: 256 },
        true, 
        ["encrypt", "decrypt"]
    )

    const keyAuth = await window.crypto.subtle.deriveKey(
        {
            name: "HKDF",
            salt: new Uint8Array(),
            info: enc.encode("key_auth"),
            hash: "SHA-256"
        },
        masterKey,
        { name: "HMAC", hash: "SHA-256", length: 256 },
        true,
        ["sign"]
    );

    return { keyEncrypt, keyAuth };
}

// ===============================
// CLIENT SIDE ENCRYPTION FUNCTION
// ===============================

async function encryptNote(password, secretText) {
    // 1. Generate Salt
    const salt = window.crypto.getRandomValues(new Uint8Array(16));

    // 2. Derive Keys
    const { keyEncrypt, keyAuth } = await deriveKeys(password, salt);

    // 3. Encrypt Secret Text
    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    const encodedText = new TextEncoder().encode(secretText);

    const encryptedBuffer = await window.crypto.subtle.encrypt(
        { name: "AES-GCM", iv: iv },
        keyEncrypt,
        encodedText
    );

    const encryptedData = new Uint8Array(iv.byteLength + encryptedBuffer.byteLength);
    encryptedData.set(iv, 0);
    encryptedData.set(new Uint8Array(encryptedBuffer), iv.byteLength);

    // 4. Create Password Validator
    const authKeyBytes = await window.crypto.subtle.exportKey("raw", keyAuth);
    const validatorBuffer = await window.crypto.subtle.digest("SHA-256", authKeyBytes);

    return {
        salt: buffToHex(salt),
        encrypted_password: buffToHex(validatorBuffer),
        encrypted_message: buffToHex(encryptedData)
    };
}


// ===============================
// CLIENT SIDE DECRYPTION FUNCTION
// ===============================

async function unlockSecureNote(password, saltHex, encryptedDataHex, encryptedPasswordHex) {
    try {
        const salt = hexToBuff(saltHex);

        // 1. Derive Keys
        const { keyEncrypt, keyAuth } = await deriveKeys(password, salt);

        // 2. Verify Password
        const authKeyBytes = await window.crypto.subtle.exportKey("raw", keyAuth);

        const computedHashBuffer = await window.crypto.subtle.digest("SHA-256", authKeyBytes);
        const computedHashHex = buffToHex(computedHashBuffer);

        if (computedHashHex !== encryptedPasswordHex) {
            throw new Error("WRONG_PASSWORD");
        }

        // 3. Decrypt
        const encryptedData = hexToBuff(encryptedDataHex);
        const iv = encryptedData.slice(0, 12);
        const ciphertext = encryptedData.slice(12);

        const decryptedBuffer = await window.crypto.subtle.decrypt(
            { name: "AES-GCM", iv: iv },
            keyEncrypt,
            ciphertext
        );

        return new TextDecoder().decode(decryptedBuffer);

    } catch (err) {
        if (err.message === "WRONG_PASSWORD") {
            console.error("Decryption failed: Incorrect password.");
            return null;
        } else {
            console.error("Decryption failed:", err);
            return null;
        }
    }
}

// =================
// EXAMPLE USAGE
// =================

(async () => {
    const password = "mySecretPassword123";
    const message = "This is my secret note!";
    
    // Encrypt
    console.log("Encrypting...");
    const encrypted = await encryptNote(password, message);
    console.log("Encrypted result:", encrypted);
    
    // Decrypt with correct password
    console.log("\nDecrypting with correct password...");
    const decrypted = await unlockSecureNote(
        password,
        encrypted.salt,
        encrypted.encrypted_message,
        encrypted.encrypted_password
    );
    console.log("Decrypted:", decrypted);
    console.log("Success:", decrypted === message);
    
    // Decrypt with wrong password
    console.log("\nDecrypting with wrong password...");
    const failed = await unlockSecureNote(
        "wrongPassword",
        encrypted.salt,
        encrypted.encrypted_message,
        encrypted.encrypted_password
    );
    console.log("Should be null:", failed === null);
})();