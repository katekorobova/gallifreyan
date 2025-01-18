# gallifreyan
This is a graphics editor designed for writing sentences in Doctor's Cot Gallifreyan, a writing system created by Brittany Goodman and inspired by the fictional Gallifreyan language from the show Doctor Who:

https://doctorscotgallifreyan.com/ 

## Exciting New Update! 🥳🎉🕺
You can now customize the color scheme of your image.

To access the settings, click Settings → Color Scheme.

After selecting your desired colors, click Apply to update the color scheme on the canvas.

![color scheme window](https://www.dropbox.com/scl/fi/bb6a0jijm4cfkiwk151wu/color_scheme_window.png?rlkey=chexgnzkg8cd2laz1dilx2jgx&st=23d9f5uy&raw=1)

## Current Features
Multiple-Word Support: Enter and visualize entire sentences in Doctor's Cot Gallifreyan.

Resizable Elements: Adjust the size of words, syllables, and inner circles for better layout control.

Element Positioning: Move and reposition various components, including words, syllables, vowels, and consonants.

Color Scheme Customization: Choose colors for various components of your image to personalize its appearance.

Image Export: Save your designs as PNG images for easy sharing and use.

Animation: Bring your sentences to life with animation feature and save them as animated GIFs.

## Future Plans
Punctuation and Number Support: Visualize numbers and punctuation marks.

More Customization Options: Introduce additional features for enhanced customization.

SVG Export: Allow designs to be exported as SVG files for higher-quality and scalable outputs.

## How to Run the Program

To run the program, make sure you have Python 3.10 or later installed on your system. First, install the required dependencies by running:
```
pip install -r requirements.txt
```
Once the dependencies are installed, run the following command from the project's root directory:
```
python -m src.main
```
## How to Use the Features
Enter the phonetic representation of your sentence by clicking the consonant and vowel buttons. Separate words with spaces and syllables with dashes. You can also remove characters from the input field as needed.

- Moving Elements: Drag syllables, consonants, and vowels to reposition them.
- Resizing Syllables: Adjust a syllable's size - along with all consecutive syllables - by dragging its border.
- Resizing Inner Circles: Modify the size of a syllable's inner circle by dragging its border.
- Resizing Words: Drag the border of the largest syllable to resize the word. Adjust the word's outer circle by dragging its border.
- Moving Words: Move an entire word by dragging the largest syllable or the empty space inside the word.

(good luck figuring it out)

Toggle the animation by clicking the Animation button.

Export your design as a PNG or GIF via File → Export as...

## Demo
![demo](https://www.dropbox.com/scl/fi/0hb3cidfjwxuaw5auudpo/demo.gif?rlkey=vyqro9jaynuhmwuqnja5i8nzj&st=djeu6w25&raw=1)

Exported PNG:

![png](https://www.dropbox.com/scl/fi/mabc7q3cv2u895xiio4sw/its_a_big_universe.png?rlkey=jyakyek6o14f5cf08367t1fb1&st=i6wnczmn&raw=1)

Exported GIF:

![gif](https://www.dropbox.com/scl/fi/btrxnlw3duwsec2kw8x3v/its_a_big_universe.gif?rlkey=0883gegfn3m3rgw7ogc5lqht3&st=syc6bwox&raw=1)
