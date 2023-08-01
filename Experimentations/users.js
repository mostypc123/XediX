// Nainštalujte balíčky pre Node.js
// npm install firebase-admin express

const express = require('express');
const admin = require('firebase-admin');

// Inicializácia aplikácie s Firebase konfiguráciou
const serviceAccount = require('./path/to/serviceAccountKey.json');
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: 'https://your-firebase-project.firebaseio.com'
});

const app = express();
app.use(express.json());

// Cesta na registráciu nového používateľa
app.post('/register', async (req, res) => {
  try {
    const { username, email, password } = req.body;
    // Vytvorenie nového používateľa s e-mailom a heslom
    await admin.auth().createUser({
      email: email,
      password: password
    });

    // Vytvorenie nového záznamu v databáze s ďalšími údajmi o používateľovi
    await admin.database().ref('users').push({
      username: username,
      email: email
    });

    return res.status(201).json({ message: 'Registrácia prebehla úspešne.' });
  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: 'Nastala chyba.' });
  }
});

// Cesta na prihlásenie používateľa (nemáme potrebu hashovať heslo, Firebase to spraví za nás)
app.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    // Prihlásenie používateľa pomocou e-mailu a hesla
    const user = await admin.auth().signInWithEmailAndPassword(email, password);

    return res.json({ message: 'Prihlásenie prebehlo úspešne.' });
  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: 'Prihlásenie zlyhalo.' });
  }
});

// Spustenie servera na porte 3000
app.listen(3000, () => {
  console.log('Server spustený na porte 3000');
});

