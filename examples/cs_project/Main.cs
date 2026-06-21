using Godot;

public partial class Main : Node2D
{
	public override void _Ready()
	{
		var bg = new ColorRect();
		bg.Color = new Color(0.20f, 0.10f, 0.30f);
		bg.Size = new Vector2(640, 360);
		AddChild(bg);

		var box = new ColorRect();
		box.Color = new Color(0.30f, 0.85f, 0.85f);
		box.Size = new Vector2(140, 140);
		box.Position = new Vector2(250, 110);
		AddChild(box);

		var lbl = new Label();
		lbl.Text = "C# scene runs (godot-kit)";
		lbl.Position = new Vector2(170, 290);
		lbl.AddThemeFontSizeOverride("font_size", 26);
		AddChild(lbl);
	}
}
