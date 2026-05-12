---
version: alpha
name: The Lobby
description: A quiet editorial civic-news system with warm neutrals, restrained contrast, and clear data-led storytelling.
colors:
  primary: "#3B3B3B"
  secondary: "#6A6A6A"
  tertiary: "#1BA54A"
  neutral: "#F9F4ED"
  surface: "#FCF9F5"
  on-surface: "#000000"
  error: "#B84A4A"
  primary-70: "#5E5E5E"
  primary-90: "#EDE9E3"
  success: "#18A84A"
  border: "#F7F1E7"
typography:
  headline-display:
    fontFamily: Switzer, Inter, -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial, sans-serif
    fontSize: 43px
    fontWeight: 400
    lineHeight: 52px
    letterSpacing: -1.701px
  headline-lg:
    fontFamily: Switzer, Inter, -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial, sans-serif
    fontSize: 35px
    fontWeight: 400
    lineHeight: 35.91px
    letterSpacing: -1.512px
  headline-md:
    fontFamily: Switzer, Inter, -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial, sans-serif
    fontSize: 29px
    fontWeight: 400
    lineHeight: 35px
  headline-sm:
    fontFamily: Switzer, Inter, -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial, sans-serif
    fontSize: 23px
    fontWeight: 400
    lineHeight: 28px
  body-lg:
    fontFamily: Switzer, Inter, -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial, sans-serif
    fontSize: 19.2px
    fontWeight: 400
    lineHeight: 28.8px
  body-md:
    fontFamily: Switzer, Inter, -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial, sans-serif
    fontSize: 16px
    fontWeight: 400
    lineHeight: 24px
  body-sm:
    fontFamily: Switzer, Inter, -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial, sans-serif
    fontSize: 14.4px
    fontWeight: 400
    lineHeight: 20px
  label-lg:
    fontFamily: Switzer, Inter, -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial, sans-serif
    fontSize: 14.4px
    fontWeight: 500
    lineHeight: 20px
    letterSpacing: 0.02em
  label-md:
    fontFamily: Switzer, Inter, -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial, sans-serif
    fontSize: 12px
    fontWeight: 500
    lineHeight: 16px
    letterSpacing: 0.06em
  label-sm:
    fontFamily: Switzer, Inter, -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial, sans-serif
    fontSize: 10px
    fontWeight: 600
    lineHeight: 12px
    letterSpacing: 0.08em
rounded:
  none: 0px
  sm: 4px
  md: 6px
  lg: 8px
  xl: 12px
  full: 9999px
spacing:
  xs: 2px
  sm: 10px
  md: 20px
  lg: 32px
  xl: 128px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.sm}"
    padding: "5px 20px"
    height: "40px"
  button-primary-hover:
    backgroundColor: "{colors.primary-70}"
    textColor: "{colors.surface}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.primary}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.sm}"
    padding: "5px 20px"
    height: "40px"
  button-link:
    backgroundColor: "transparent"
    textColor: "{colors.primary}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.none}"
    padding: "0px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
    padding: "20px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.sm}"
    padding: "10px"
  chip:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.secondary}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
  badge-success:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
  legend-dot:
    backgroundColor: "{colors.tertiary}"
    rounded: "{rounded.full}"
    size: "8px"
# The Lobby

## Overview
The Lobby feels like a calm civic editorial product: intelligent, factual, and slightly formal, but still approachable. It uses a spacious canvas, large restrained headlines, and data-visual storytelling to make complex government information feel legible rather than intimidating. The tone is professional and trust-building, with enough warmth in the background and card surfaces to keep it from feeling sterile.

## Colors
- **Primary (#3B3B3B):** The core ink tone used for body text, navigation, buttons, and most structural UI. It reads as softer than pure black, which helps the experience feel editorial and human.
- **Secondary (#6A6A6A):** A muted gray for supporting text, metadata, and less prominent labels. It keeps hierarchy clear without introducing visual noise.
- **Tertiary (#1BA54A):** A confident civic green used for positive vote states, success indicators, and chart emphasis. It provides the clearest brand accent in the interface.
- **Neutral (#F9F4ED):** The warm page background. This creamy off-white creates a newspaper-like tone and reduces contrast harshness.
- **Surface (#FCF9F5):** Card and panel backgrounds sit just above the page tone, preserving a subtle layered look.
- **On-surface (#000000):** Reserved for the strongest chart marks and selected high-contrast details where absolute clarity matters.
- **Border (#F7F1E7):** A faint warm border color for cards, inputs, and separators. It supports structure without looking rigid.
- **Error (#B84A4A):** A subdued red reserved for negative states and exceptions. It should remain rare to preserve the calm tone.

## Typography
Switzer is the primary typeface, with Inter and common system sans fallbacks to preserve consistency. The system is light in weight overall: headlines are typically 400, while labels move up to 500 or 600 for clarity and scannability. Large headings rely on tight negative letter spacing, which gives the editorial masthead and hero copy a polished, contemporary feel.

Headlines scale from the 43px display style down to 23px subheads, all remaining crisp and minimal rather than decorative. Body copy is comfortable and readable at 19.2px with generous 28.8px line height, which suits the long-form civic context. Labels and UI metadata use smaller sizes with subtle tracking, especially in uppercase-like navigation and chip treatments, to create a measured institutional voice.

## Layout & Spacing
The layout favors a wide, airy desktop composition with strong left/right content separation and large vertical breathing room. Content blocks are aligned to a loose grid rather than a rigid dense system, allowing the hero text, data card, and later content sections to feel independent but balanced. The spacing rhythm is anchored by 2px, 10px, 20px, 32px, and a large 128px section gap, which creates a calm editorial cadence.

Cards use internal padding of 20px and sit on the slightly lighter surface color to distinguish them from the page background. Navigation and utility clusters use compact spacing, while major page transitions use generous whitespace to emphasize headlines and charts. The result is spacious without feeling empty.

## Elevation & Depth
Depth is intentionally minimal. Instead of dramatic shadows, the design relies on tonal layering: warm background, lighter surface panels, and faint borders. Small shadows appear only as subtle elevation cues in top navigation and card-like regions, keeping the interface grounded and trustworthy.

This flat treatment suits the civic-news subject matter, where clarity should outrank ornament. Hierarchy comes from contrast, scale, and spacing rather than from strong depth effects. Use borders and soft surface shifts before reaching for shadow.

## Shapes
The shape language is understated and pragmatic. Corner radii stay small, with 4px on buttons and 6px on cards, giving the interface a lightly rounded but still disciplined feel. This creates a measured, institutional look that avoids either harsh sharpness or playful softness.

Pills, status chips, and legend markers follow the same restrained logic, using small radii or full circles only when the shape serves a semantic purpose. Overall, the geometry should feel tidy, precise, and quietly confident.

## Components
Buttons are compact and text-first. Primary buttons use the dark primary fill with light text, 4px rounding, and a 40px touch target; they should feel decisive but not loud. Secondary buttons invert the treatment with a transparent background and primary-colored text/border. Link buttons are minimal, using no border, no fill, and underlined text for low-priority actions.

Cards use the surface color, a 1px warm border, 6px radius, and 20px padding. They should feel like clipped editorial containers rather than elevated widgets. Use cards to frame bills, roll calls, and data panels without adding heavy shadow treatment.

Inputs should match cards in tone: light surface, soft border, and small corner radius. Keep controls visually quiet so the content remains the focus. If states are needed, prefer border and text color shifts over filled backgrounds.

Chips and badges should stay small and restrained. Status chips can use neutral or success greens with compact padding, while the passed-state badge should use the tertiary green to signal positive outcomes. In charts and legends, use small circular markers and rely on color consistency to communicate vote categories clearly.

Navigation should be simple and text-led, with no decorative chrome. Use the primary ink tone for links and keep hover states subtle. For data visualizations, preserve the strong black/green contrast already established in the screenshot, and avoid introducing extra palette colors unless they are semantically necessary.

## Do's and Don'ts
- Do keep the interface spacious and editorial, with clear separation between major story blocks.
- Do use warm neutrals and soft borders to support readability and calm the visual tone.
- Do reserve the tertiary green for positive, civic, or confirmed states.
- Do use Switzer for all typography and maintain the restrained weight progression.
- Don't introduce strong shadows, glossy gradients, or high-contrast neon accents.
- Don't make buttons overly tall, pill-shaped, or visually dominant.
- Don't collapse whitespace around headlines and charts; the layout depends on air.
- Don't use pure black for most text when the softer primary ink is more appropriate.