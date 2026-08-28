# Keep the inference product in a standalone repository

The inference application is maintained as an independent nested Git repository rather than being added to the parent Streamlit training repository. This prevents competition-facing product work from mixing with training experiments and lets the application later be versioned, packaged, or published independently while consuming a controlled Production Model release.

