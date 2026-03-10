import React from "react";

export const markdownComponents = {
  table: (props: React.ComponentPropsWithoutRef<'table'>) => <div className="overflow-x-auto my-4 rounded-lg border border-gray-700/50"><table className="w-full text-left border-collapse" {...props} /></div>,
  thead: (props: React.ComponentPropsWithoutRef<'thead'>) => <thead className="bg-gray-800/80 text-gray-200 text-xs uppercase font-medium" {...props} />,
  th: (props: React.ComponentPropsWithoutRef<'th'>) => <th className="px-4 py-3 border-b border-gray-700/50" {...props} />,
  td: (props: React.ComponentPropsWithoutRef<'td'>) => <td className="px-4 py-3 border-b border-gray-700/50 text-gray-300 text-sm align-top leading-relaxed" {...props} />,
  tr: (props: React.ComponentPropsWithoutRef<'tr'>) => <tr className="hover:bg-gray-800/40 transition-colors" {...props} />,
  p: (props: React.ComponentPropsWithoutRef<'p'>) => <p className="mb-3 leading-relaxed text-gray-300" {...props} />,
  h1: (props: React.ComponentPropsWithoutRef<'h1'>) => <h1 className="text-lg font-bold mt-5 mb-3 text-white" {...props} />,
  h2: (props: React.ComponentPropsWithoutRef<'h2'>) => <h2 className="text-base font-semibold mt-4 mb-2 text-indigo-300" {...props} />,
  h3: (props: React.ComponentPropsWithoutRef<'h3'>) => <h3 className="text-sm font-semibold mt-3 mb-2 text-indigo-200" {...props} />,
  ul: (props: React.ComponentPropsWithoutRef<'ul'>) => <ul className="list-disc list-inside space-y-1 mb-3 ml-1 text-gray-300" {...props} />,
  ol: (props: React.ComponentPropsWithoutRef<'ol'>) => <ol className="list-decimal list-inside space-y-1 mb-3 ml-1 text-gray-300" {...props} />,
  li: (props: React.ComponentPropsWithoutRef<'li'>) => <li className="leading-relaxed" {...props} />,
  strong: (props: React.ComponentPropsWithoutRef<'strong'>) => <strong className="font-semibold text-gray-100" {...props} />,
  blockquote: (props: React.ComponentPropsWithoutRef<'blockquote'>) => <blockquote className="border-l-2 border-indigo-500 pl-3 py-1 italic text-gray-400 my-3" {...props} />,
  hr: (props: React.ComponentPropsWithoutRef<'hr'>) => <hr className="border-gray-700 my-4" {...props} />,
};
