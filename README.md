# eziri

Version 1.0.0 2026-06-29

### Usage 
```
eziri \path\to\image image-width image-height
```

This is a small program for automatically analyzing iri images using the watershed algorithm.
It has an advantage over other automated IRI analyses in its tolerance for blurry images.
It calculates the area, perimeter, and eccentricity of each crystal, which it outputs as a CSV.
Images to analyze must be in the same directory as, or in a subdirectory of, the directory containing run.py and eziri.

- [This program's goal is to offload tedious ImageJ work. It isn't better than you at this, it just doesn't get tired.]
- [Eziri cannot save bad images. If you can't count it, eziri can't either. Even if you have a hard time discerning between crystals, eziri probably won't work.]

### BEFORE YOU RUN:
- [Touch up your images before running eziri, make sure any space you don't want measured is as black as possible.]
- [Run this through ImageJ first. Eziri needs the real-life image dimensions to calculate crystal areas and perimeters.]
- [Eziri uses numpy, scipy, and scikit-image. If you do not have these installed, run pip install -r required_packages.]
		


