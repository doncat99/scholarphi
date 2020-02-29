from dataclasses import dataclass
from typing import Any, Callable, Dict, List, NamedTuple, Optional

"""
FILE PROCESSING
"""

ArxivId = str
Path = str
AbsolutePath = str
RelativePath = str


@dataclass(frozen=True)
class FileContents:

    path: Path
    " Relative or absolute; depends on the path passed in for file reading. "

    contents: str
    " Contents of the file. "

    encoding: str
    " Character encoding of the file. "


@dataclass(frozen=True)
class OutputFile:
    output_type: str
    " Type of file output by running TeX (e.g., 'ps', 'pdf')"

    path: RelativePath
    """
    Path to file relative to the compilation directory. In most cases, this will
    either be relative to <data-directory>/<arxiv-id>, or to
    <data-directory>/<arxiv-id>/<iteration>/.
    """


@dataclass(frozen=True)
class CompilationResult:
    success: bool
    output_files: List[OutputFile]
    stdout: bytes
    stderr: bytes


"""
SEMANTIC SCHOLAR API
"""

S2Id = str
S2AuthorId = str


@dataclass(frozen=True)
class Author:
    id: Optional[S2AuthorId]
    name: str


@dataclass(frozen=True)
class Reference:
    s2_id: S2Id
    arxivId: ArxivId
    doi: str
    title: str
    authors: List[Author]
    venue: str
    year: int


@dataclass(frozen=True)
class SerializableReference:
    s2_id: S2Id
    arxivId: ArxivId
    doi: str
    title: str
    authors: str
    " Should be a literal string representing a Python list that can be read with ast.literal_eval "
    venue: str
    year: int


@dataclass(frozen=True)
class S2Metadata:
    s2_id: S2Id
    references: List[Reference]


"""
CITATIONS
"""


@dataclass(frozen=True)
class Bibitem:
    key: str

    text: str
    " Plaintext extracted for bibitem. "


@dataclass(frozen=True)
class BibitemMatch:
    key: str
    bibitem_text: str
    s2_id: str
    s2_title: str


"""
TEX PARSING
"""

TexFileName = str
TexContents = str


@dataclass(frozen=True)
class CharacterRange:
    start: int
    "Character position where this range begins in the TeX."

    end: int
    "Character position where this range ends in the TeX."


@dataclass(frozen=True)
class Entity(CharacterRange):
    """
    Every entity has, at the least, a start and end position.
    """


@dataclass(frozen=True)
class SerializableEntity(Entity):
    """
    If they are to be saved and loaded to the file system, entities should have additional
    information that can uniquely identify them (tex_path, id_), and a raw representation of
    their contents (tex, content_tex). The unique identifier will be key in later stages of
    the pipeline for linking information about the entity with its hue from colorization and the
    bounding boxes detected for the entitiy.
    """

    tex_path: str
    """
    The path to the TeX file this entity was found in. Should be a short path, relative to the 
    directory of sources this TeX file is in, not relative to the data directory, and not
    relative to the source code directory for this project.
    """

    id_: str
    """
    An ID which, when combined with the TeX path and arXiv ID for this entity, can uniquely
    identify the entity. In many cases, this will simply be a stringified index of which entity
    in the TeX file this is (e.g., 0, 1, 2, ...).
    """

    tex: str
    " The TeX for the detected entity. "

    context_tex: str
    """
    Context around the position where this entity was extracted from. It's recommended that
    at least 20 characters to the left and right are included.
    """


@dataclass(frozen=True)
class HueIteration:
    hue: float
    iteration: str


@dataclass(frozen=True)
class Equation(SerializableEntity):
    i: int
    " Index of this equation in the TeX document. "

    content_start: int
    " Index of character where the contents (i.e. 'content_tex') of the equation starts. "

    content_end: int
    " Index of character where the contents of the equation ends. "

    content_tex: str
    " TeX for the equation contents, inside the environment (e.g., 'x + y'). "

    katex_compatible_tex: str
    " A santized version of the equation content meant for KaTeX parsing. "

    depth: int
    """
    Depth within a tree of equations. Most equations will not be nested in others, so will have a
    depth of 0 if not nested in another equation. As an example, if this equation is nested in
    another equation, which is nested in another equation, it will have a depth of 2.
    """


@dataclass(frozen=True)
class LengthAssignment(Entity):
    pass


@dataclass(frozen=True)
class BeginDocument(Entity):
    pass


@dataclass(frozen=True)
class Documentclass(Entity):
    pass


@dataclass(frozen=True)
class MacroDefinition:
    name: str
    " Name of macro. For example, 'omega' if you want to detect \\omega{}. "

    parameter_string: str
    " Parameter string for macro, in TeX format, e.g., '[#1]#2'. As with TeX, can be empty string. "


@dataclass(frozen=True)
class Macro(Entity):
    tex: str


"""
EQUATION PARSING
"""

EquationIndex = int
CharacterIndex = int
SymbolIndex = int


class CharacterId(NamedTuple):
    tex_path: str
    equation_index: EquationIndex
    character_index: CharacterIndex


@dataclass(frozen=True)
class SymbolId:
    tex_path: str
    equation_index: EquationIndex
    symbol_index: SymbolIndex


class Character(NamedTuple):
    text: str
    i: CharacterIndex
    start: int
    end: int


@dataclass(frozen=True)
class TokenWithOrigin:
    """
    A token and a character are the same thing, it just has two names for historical reasons.
    """

    tex_path: str
    equation: Equation
    token_index: int
    start: int
    end: int
    text: str


MathML = str


class Symbol(NamedTuple):
    characters: List[CharacterIndex]
    mathml: MathML
    children: List[Any]
    """
    List of child symbols. Should be of type 'Symbol'. 'children' is a bit of misnomer. These is
    actually a list of all other symbols for which this is the closest ancestor.
    """


class SymbolWithId(NamedTuple):
    symbol_id: SymbolId
    symbol: Symbol


@dataclass(frozen=True)
class EquationId:
    tex_path: str
    equation_index: int


" Serializable data classes for symbols, for storing results to file"


@dataclass(frozen=True)
class SerializableToken:
    tex_path: str
    equation: str
    equation_index: int
    token_index: int
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class SerializableSymbol(SymbolId):
    equation: str
    mathml: str


@dataclass(frozen=True)
class SerializableCharacter(SymbolId):
    equation: str
    character_index: int


@dataclass(frozen=True)
class SerializableChild(SymbolId):
    equation: str
    child_index: int


"""
COLORIZATION RECORDS
"""

Hue = float


@dataclass(frozen=True)
class ColorizedTokenWithOrigin:
    tex_path: str
    equation_index: int
    token_index: int
    start: int
    end: int
    text: str
    hue: Hue


@dataclass(frozen=True)
class ColorizationRecord:
    tex_path: str
    iteration: str
    hue: float
    entity_id: str
    " Should match the ID on a 'SerializableEntity'"


@dataclass(frozen=True)
class EquationTokenColorizationRecord(ColorizationRecord, ColorizedTokenWithOrigin):
    pass


"""
SEARCH
"""


@dataclass(frozen=True)
class Match:
    """
    A MathML equation that matches a queried MathML equation. Rank is relative to the set of
    MathML equations it was chosen from. Rank starts at 1.
    """

    queried_mathml: MathML
    matching_mathml: MathML
    rank: int


Matches = Dict[MathML, List[Match]]


"""
IMAGE PROCESSING
"""


class Point(NamedTuple):
    """
    Location of a pixel within an image.
    """

    x: int
    y: int


@dataclass(frozen=True)
class Rectangle:
    """
    Rectangle within an image. Left and top refer to positions of pixels.
    """

    left: int
    top: int
    width: int
    height: int


@dataclass(frozen=True)
class FloatRectangle:
    left: float
    top: float
    width: float
    height: float


@dataclass(frozen=True)
class BoundingBox(FloatRectangle):
    """
    Bounding box for an entity. Left, top, width, and height are all expressed on a range of
    0..1, where 0 is all the way to the top/left, and 1 is all the way to the bottom/right.
    Bounding boxes are expressed with these ratio dimensions instead of absolute dimensions
    as it's much easier, and accurate enough. To get absolute dimensions in PDF coordinates
    would require us to add to our pipeline a way of detecting the PDF dimensions of all
    files output by the TeX compiler (i.e. for both PDFs and PostScript), which requires
    dependence on external tools like GhostScript. Ratio dimensions can be detected in the
    exact same way for all output files, as long as we can raster them to PNGs.
    """

    page: int


@dataclass(frozen=True)
class BoundingBoxAndHue:
    hue: float
    box: BoundingBox


@dataclass(frozen=True)
class HueLocationInfo(BoundingBox, ColorizationRecord):
    relative_file_path: str


CharacterLocations = Dict[CharacterId, List[BoundingBox]]


@dataclass(frozen=True)
class CitationLocation(BoundingBox):
    key: str
    cluster_index: int


@dataclass(frozen=True)
class SymbolLocation(SymbolId, BoundingBox):
    pass


"""
DATABASE UPLOADS
"""


@dataclass(frozen=True)
class EntityInfo:
    colorization_record: ColorizationRecord
    hue_location_infos: List[HueLocationInfo]


@dataclass(frozen=True)
class PaperProcessingSummary:
    arxiv_id: ArxivId
    s2_id: S2Id
    entity_infos: List[EntityInfo]


EntityUploadCallable = Callable[[PaperProcessingSummary], None]
