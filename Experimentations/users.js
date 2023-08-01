// Import balíčkov
const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const bcrypt = require('bcrypt');

// Inicializácia Express aplikácie
const app = express();
app.use(express.json());

// Vytvorenie pripojenia k SQLite3 databáze
const db = new sqlite3.Database('users.db');

// Cesta na registráciu nového používateľa
app.post('/register', async (req, res) => {
  try {
    const { username, email, password } = req.body;
    // Hashovanie hesla
    const hashedPassword = await bcrypt.hash(password, 10);

    // Uloženie používateľa do databázy
    db.run(
      'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
      [username, email, hashedPassword],
      (err) => {
        if (err) {
          console.error(err.message);
          return res.status(500).json({ error: 'Registrácia zlyhala.' });
        }
        return res.status(201).json({ message: 'Registrácia prebehla úspešne.' });
      }
    );
  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: 'Nastala chyba.' });
  }
});

// Cesta na prihlásenie používateľa
app.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;

    // Získanie uloženého hesla z databázy na základe používateľského mena
    db.get('SELECT password FROM users WHERE username = ?', [username], async (err, row) => {
      if (err) {
        console.error(err.message);
        return res.status(500).json({ error: 'Prihlásenie zlyhalo.' });
      }

      // Porovnanie zadaného hesla s uloženým hashom
      if (!row) {
        return res.status(404).json({ error: 'Používateľ neexistuje.' });
      }
      const passwordMatch = await bcrypt.compare(password, row.password);

      if (!passwordMatch) {
        return res.status(401).json({ error: 'Nesprávne heslo.' });
      }

      return res.json({ message: 'Prihlásenie prebehlo úspešne.' });
    });
  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: 'Nastala chyba.' });
  }
});

// Spustenie servera na porte 3000
app.listen(3000, () => {
  console.log('Server spustený na porte 3000');
});
