import { useState } from "react";
import { Github, Linkedin, Shield, ExternalLink } from "lucide-react";

const TEAM = [
  {
    name: "Shailav",
    photo: "/team/shailav.jpg",
    initial: "S",
    color: "from-blue-500 to-cyan-400",
    linkedin: "https://linkedin.com/in/shailav",
  },
  {
    name: "Bhupendra",
    photo: "/team/bhupendra.jpg",
    initial: "B",
    color: "from-purple-500 to-pink-400",
    linkedin: "https://linkedin.com/in/bhupendra",
  },
  {
    name: "Shivam",
    photo: "/team/shivam.jpg",
    initial: "S",
    color: "from-emerald-500 to-teal-400",
    linkedin: "https://linkedin.com/in/shivam",
  },
  {
    name: "Gungun",
    photo: "/team/gungun.jpg",
    initial: "G",
    color: "from-amber-500 to-orange-400",
    linkedin: "https://linkedin.com/in/gungun",
  },
];

const GITHUB_URL = "https://github.com";

function TeamCard({ member, delay }) {
  const [imgError, setImgError] = useState(false);

  return (
    <div
      className="glass rounded-2xl p-6 text-center card-hover animate-fade-in"
      style={{ animationDelay: `${delay}ms`, animationFillMode: "both" }}>
      {/* Photo with glow */}
      <div className="relative mx-auto w-24 h-24 mb-4">
        <div
          className={`absolute inset-[-4px] rounded-full bg-gradient-to-br ${member.color} opacity-25 blur-lg`}
        />
        {!imgError ?
          <img
            src={member.photo}
            alt={member.name}
            className="relative w-24 h-24 rounded-full object-cover border-2 border-white/10 shadow-xl"
            onError={() => setImgError(true)}
          />
        : <div
            className={`relative w-24 h-24 rounded-full bg-gradient-to-br ${member.color} flex items-center justify-center text-white font-bold text-3xl shadow-xl border-2 border-white/10`}>
            {member.initial}
          </div>
        }
      </div>

      {/* Name */}
      <h4 className="text-base font-semibold text-white">{member.name}</h4>

      {/* LinkedIn */}
      <a
        href={member.linkedin}
        target="_blank"
        rel="noreferrer"
        className="inline-flex items-center gap-1.5 mt-3 px-3 py-1.5 rounded-lg bg-blue-500/[0.08] border border-blue-500/15 text-xs text-blue-400 hover:text-blue-300 hover:bg-blue-500/[0.15] transition-all">
        <Linkedin size={12} />
        LinkedIn
      </a>
    </div>
  );
}

export default function AboutView() {
  return (
    <div className="p-4 md:p-8 space-y-8 animate-fade-in max-w-4xl mx-auto">
      {/* Project header */}
      <div className="glass rounded-2xl p-8 glow-border text-center">
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Shield size={24} className="text-white" />
          </div>
          <div className="text-left">
            <h2 className="text-2xl font-bold text-gradient">200 Hustlers</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              India AI Impact Buildathon — Problem Statement 2
            </p>
          </div>
        </div>
        <p className="text-sm text-slate-400 max-w-xl mx-auto leading-relaxed mt-2">
          <span className="text-white font-medium">TrustHoneypot</span> is an
          agentic scam intelligence platform that engages fraudsters with
          believable AI conversations, extracts critical financial data like UPI
          IDs and bank accounts, and classifies 18+ scam categories — protecting
          Indian citizens from digital fraud in real-time.
        </p>
        <a
          href={GITHUB_URL}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-2 mt-5 px-5 py-2.5 rounded-xl bg-white/[0.04] border border-slate-700/40 text-xs font-medium text-slate-300 hover:text-white hover:border-slate-500 hover:bg-white/[0.07] transition-all">
          <Github size={14} />
          View on GitHub
          <ExternalLink size={10} className="opacity-50" />
        </a>
      </div>

      {/* Team */}
      <div>
        <h3 className="text-sm font-semibold text-slate-300 text-center mb-6 uppercase tracking-wider">
          Meet the Team
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {TEAM.map((member, i) => (
            <TeamCard key={member.name} member={member} delay={i * 120} />
          ))}
        </div>
      </div>
    </div>
  );
}
