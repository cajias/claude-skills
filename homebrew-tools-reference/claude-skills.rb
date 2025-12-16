class ClaudeSkills < Formula
  desc "Collection of skills to expand Claude's capabilities for specific workflows and tasks"
  homepage "https://github.com/cajias/claude-skills"
  url "https://github.com/cajias/claude-skills/archive/refs/tags/v1.0.0.tar.gz" # Will be automatically updated by GitHub Actions
  sha256 "0000000000000000000000000000000000000000000000000000000000000000" # Will be automatically updated by GitHub Actions
  version "1.0.0" # Will be automatically updated by GitHub Actions
  license "MIT"

  def install
    # Install all skill directories
    (share/"claude-skills"/"skills").install Dir["skills/*"]
    
    # Install all plugin directories
    (share/"claude-skills"/"plugins").install Dir["plugins/*"]
    
    # Install documentation
    (share/"claude-skills").install "README.md"
    (share/"claude-skills").install "LICENSE"
  end

  def caveats
    <<~EOS
      Claude Skills installed successfully!

      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

      📦 USAGE:
        Skills and plugins are installed at:
          #{share}/claude-skills/

        📚 Skills: #{share}/claude-skills/skills/
        🔌 Plugins: #{share}/claude-skills/plugins/

      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

      🎯 AVAILABLE SKILLS:
        • GitHub Issue Grooming
        • Software Effort Estimation & Codebase Valuation
        • AI Writing Humanizer

      🔌 AVAILABLE PLUGINS:
        • PR Monitor

      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

      📖 To use plugins:
        claude plugin install \\
          https://github.com/cajias/claude-skills/tree/main/plugins/PLUGIN_NAME

      📖 Learn more: https://github.com/cajias/claude-skills
    EOS
  end

  test do
    assert_predicate share/"claude-skills/README.md", :exist?
    assert_predicate share/"claude-skills/skills", :exist?
    assert_predicate share/"claude-skills/plugins", :exist?
  end
end
