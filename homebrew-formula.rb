class Repo2context < Formula
  include Language::Python::Virtualenv

  desc "One-command repo → Markdown context generator for LLM workflows"
  homepage "https://github.com/AdiMilstein/repo2context"
  url "https://files.pythonhosted.org/packages/source/r/repo2context/repo2context-0.1.0.tar.gz"
  sha256 "1b5c2a92058360e7c4fbaf442a2a5aec0feb31acf9ceb59ad185ea9f7d19850c"
  license "MIT"

  depends_on "python@3.11"

  resource "pathspec" do
    url "https://files.pythonhosted.org/packages/source/p/pathspec/pathspec-0.11.2.tar.gz"
    sha256 "e0d8d0ac2f12da61956eb2306b69f9469b42f4deb0f3cb6ed47b9cce9996ced3"
  end

  resource "tiktoken" do
    url "https://files.pythonhosted.org/packages/source/t/tiktoken/tiktoken-0.5.2.tar.gz"
    sha256 "f54c581f134a8ea96ce2023ab221d4d4d81ab614efa0b2fbce926387deb56c80"
  end

  def install
    virtualenv_install_with_resources
  end

  def caveats
    <<~EOS
      To enable AI-powered file summaries, install the OpenAI package:
        #{libexec}/bin/pip install openai

      Then set your OpenAI API key:
        export OPENAI_API_KEY="your-api-key-here"

      Use the --summary flag to generate intelligent file summaries:
        repo2context --summary
    EOS
  end

  test do
    # Test basic functionality
    system bin/"repo2context", "--help"
    assert_match "repo2context", shell_output("#{bin}/repo2context --version")
  end
end 