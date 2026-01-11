# Running HYROX Course Correct Locally

## Quick Start (3 Steps)

### 1. Install Dependencies

Open your terminal and navigate to the project directory:

```bash
cd /Users/dutch/Workspace/hyroxcoursecorrect
pip install -r requirements.txt
```

This installs Flask and all required Python packages.

### 2. Start the Web Server

```bash
cd web
python app.py
```

You should see output like:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### 3. Open in Browser

Open your web browser and go to:
```
http://localhost:5000
```

or

```
http://127.0.0.1:5000
```

That's it! The app is now running locally on your machine.

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

## Troubleshooting

### Port Already in Use

If you see an error like "Address already in use", another application is using port 5000. 

**Solution**: Edit `web/app.py` and change the port:

```python
# Change this line at the bottom of app.py:
app.run(debug=True, host='127.0.0.1', port=5001)  # Use 5001 instead
```

Then access the app at `http://localhost:5001`

### Module Not Found Errors

If you see "ModuleNotFoundError: No module named 'flask'":

**Solution**: Make sure you installed the requirements:
```bash
pip install -r requirements.txt
```

If using a virtual environment, activate it first:
```bash
source .venv/bin/activate  # On Mac/Linux
# or
.venv\Scripts\activate  # On Windows
```

### Venue Handicaps Not Loading

If the app shows "Unknown venue" errors:

**Solution**: Make sure the handicap data exists:
```bash
# Generate sample data and handicaps
python execution/generate_sample_data.py
python execution/clean_hyrox_data.py --input .tmp/raw_results_combined.csv --output .tmp/cleaned_results.csv
python execution/build_handicap_model.py --input .tmp/cleaned_results.csv --output .tmp/venue_handicaps.csv
```

## Development Mode

The app runs in debug mode by default, which means:
- ✅ Auto-reloads when you change code
- ✅ Detailed error messages
- ⚠️ Should NOT be used in production

## Accessing from Other Devices

To access the app from other devices on your network:

1. Edit `web/app.py` and change:
   ```python
   app.run(debug=True, host='0.0.0.0', port=5000)
   ```

2. Find your computer's IP address:
   ```bash
   # On Mac:
   ifconfig | grep "inet "
   
   # On Windows:
   ipconfig
   ```

3. On other devices, go to:
   ```
   http://YOUR_IP_ADDRESS:5000
   ```

## Next Steps

- Customize the venue list in `web/app.py`
- Update course factors by running the full pipeline
- Deploy to a cloud platform for public access

## Need Help?

Check the main [README.md](../README.md) for more information or open an issue on GitHub.
